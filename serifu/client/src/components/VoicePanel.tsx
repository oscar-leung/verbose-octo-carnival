import { useEffect, useRef, useState } from 'react';
import type { RoomUser } from '../../../shared/types';
import type { RoomActions, SignalHandler } from '../lib/useRoom';
import { VoiceMesh } from '../lib/voice';

interface Props {
  selfId: string;
  users: RoomUser[];
  actions: RoomActions;
  onSignal: (handler: SignalHandler) => () => void;
}

export default function VoicePanel({ selfId, users, actions, onSignal }: Props) {
  const meshRef = useRef<VoiceMesh | null>(null);
  const [joined, setJoined] = useState(false);
  const [muted, setMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streams, setStreams] = useState<Map<string, MediaStream>>(new Map());

  const stopVoice = () => {
    meshRef.current?.stop();
    meshRef.current = null;
    setStreams(new Map());
    setJoined(false);
    setMuted(false);
    actions.setVoiceState(false, false);
  };

  const joinVoice = async () => {
    setError(null);
    const mesh = new VoiceMesh(selfId, actions.sendSignal, (peerId, stream) => {
      setStreams((prev) => {
        const next = new Map(prev);
        if (stream) next.set(peerId, stream);
        else next.delete(peerId);
        return next;
      });
    });
    try {
      await mesh.start();
    } catch {
      setError('マイクが使えないみたい — mic permission denied or unavailable.');
      return;
    }
    meshRef.current = mesh;
    setJoined(true);
    actions.setVoiceState(true, false);
  };

  const toggleMute = () => {
    const next = !muted;
    setMuted(next);
    meshRef.current?.setMuted(next);
    actions.setVoiceState(true, next);
  };

  // Route signaling messages into the mesh while joined.
  useEffect(() => {
    if (!joined) return;
    const unsubscribe = onSignal((from, data) => meshRef.current?.handleSignal(from, data));
    return unsubscribe;
  }, [joined, onSignal]);

  // Keep peer connections in sync with who is in voice right now.
  useEffect(() => {
    if (!joined) return;
    meshRef.current?.syncPeers(users.filter((u) => u.inVoice && u.id !== selfId).map((u) => u.id));
  }, [joined, users, selfId]);

  // If our socket identity changes (reconnect) or the panel unmounts, tear down.
  useEffect(() => {
    return () => {
      meshRef.current?.stop();
      meshRef.current = null;
    };
  }, [selfId]);

  const othersInVoice = users.filter((u) => u.inVoice && u.id !== selfId).length;

  return (
    <div className="voice-panel">
      {joined ? (
        <>
          <button className={muted ? 'chip warn' : 'chip'} onClick={toggleMute}>
            {muted ? '🔇 unmute' : '🎙 mute'}
          </button>
          <button className="chip" onClick={stopVoice}>
            leave voice
          </button>
          <span className="muted">
            {othersInVoice > 0
              ? `${othersInVoice} other${othersInVoice > 1 ? 's' : ''} in voice`
              : 'you are alone in voice so far'}
          </span>
        </>
      ) : (
        <>
          <button className="primary" onClick={() => void joinVoice()}>
            🎙 ボイス参加 / join voice
          </button>
          <span className="muted">talk while you watch — pause anytime to discuss a line</span>
        </>
      )}
      {error && <span className="error">{error}</span>}
      {[...streams.entries()].map(([peerId, stream]) => (
        <AudioSink key={peerId} stream={stream} />
      ))}
    </div>
  );
}

function AudioSink({ stream }: { stream: MediaStream }) {
  const ref = useRef<HTMLAudioElement | null>(null);
  useEffect(() => {
    if (ref.current) ref.current.srcObject = stream;
  }, [stream]);
  return <audio ref={ref} autoPlay />;
}
