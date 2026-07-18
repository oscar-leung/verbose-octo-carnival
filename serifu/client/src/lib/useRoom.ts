import { useEffect, useMemo, useRef, useState } from 'react';
import { io, type Socket } from 'socket.io-client';
import type {
  ClientToServerEvents,
  RoomState,
  ServerToClientEvents,
  SignalData,
  SkitScript,
  SpeechAttempt,
} from '../../../shared/types';

export type AppSocket = Socket<ServerToClientEvents, ClientToServerEvents>;

export type SignalHandler = (from: string, data: SignalData) => void;

export type SpeechAttemptEvent = SpeechAttempt & { userId: string; userName: string };
export type SpeechAttemptHandler = (attempt: SpeechAttemptEvent) => void;

export interface RoomActions {
  play(position: number): void;
  pause(position: number): void;
  seek(position: number): void;
  setRehearsal(enabled: boolean): void;
  rehearsalPause(lineId: string): void;
  rehearsalResume(): void;
  claim(characterId: string): void;
  release(characterId: string): void;
  loadScript(script: SkitScript): Promise<{ ok: boolean; error?: string }>;
  setVoiceState(inVoice: boolean, muted: boolean): void;
  sendSignal(to: string, data: SignalData): void;
  sendSpeechAttempt(attempt: SpeechAttempt): void;
}

export interface RoomConnection {
  connected: boolean;
  selfId: string | null;
  state: RoomState | null;
  script: SkitScript | null;
  joinError: string | null;
  actions: RoomActions;
  /** Subscribe to WebRTC signaling messages; returns an unsubscribe fn. */
  onSignal(handler: SignalHandler): () => void;
  /** Subscribe to spoken-line attempts from the room; returns an unsubscribe fn. */
  onSpeechAttempt(handler: SpeechAttemptHandler): () => void;
  /** Estimated server clock (ms epoch), for playback extrapolation. */
  serverNow(): number;
}

export function useRoom(roomId: string, name: string): RoomConnection {
  const socketRef = useRef<AppSocket | null>(null);
  const clockOffsetRef = useRef(0);
  const signalHandlersRef = useRef(new Set<SignalHandler>());
  const speechHandlersRef = useRef(new Set<SpeechAttemptHandler>());
  const [connected, setConnected] = useState(false);
  const [selfId, setSelfId] = useState<string | null>(null);
  const [state, setState] = useState<RoomState | null>(null);
  const [script, setScript] = useState<SkitScript | null>(null);
  const [joinError, setJoinError] = useState<string | null>(null);

  useEffect(() => {
    const socket: AppSocket = io();
    socketRef.current = socket;

    const join = () => {
      socket.emit('room:join', { roomId, name }, (r) => {
        if (r.ok) {
          clockOffsetRef.current = r.state.serverNow - Date.now();
          setSelfId(r.selfId);
          setState(r.state);
          setScript(r.script);
          setJoinError(null);
        } else {
          setJoinError(r.error);
        }
      });
    };

    socket.on('connect', () => {
      setConnected(true);
      join();
    });
    socket.on('disconnect', () => {
      setConnected(false);
    });
    socket.on('room:state', (s) => {
      clockOffsetRef.current = s.serverNow - Date.now();
      setState(s);
    });
    socket.on('script:state', (s) => {
      setScript(s);
    });
    socket.on('webrtc:signal', ({ from, data }) => {
      for (const handler of signalHandlersRef.current) handler(from, data);
    });
    socket.on('speech:attempt', (attempt) => {
      for (const handler of speechHandlersRef.current) handler(attempt);
    });

    return () => {
      socket.close();
      socketRef.current = null;
      setConnected(false);
      setState(null);
      setSelfId(null);
    };
  }, [roomId, name]);

  const actions = useMemo<RoomActions>(
    () => ({
      play: (position) => socketRef.current?.emit('playback:play', { position }),
      pause: (position) => socketRef.current?.emit('playback:pause', { position }),
      seek: (position) => socketRef.current?.emit('playback:seek', { position }),
      setRehearsal: (enabled) => socketRef.current?.emit('rehearsal:set', { enabled }),
      rehearsalPause: (lineId) => socketRef.current?.emit('rehearsal:pause', { lineId }),
      rehearsalResume: () => socketRef.current?.emit('rehearsal:resume'),
      claim: (characterId) => socketRef.current?.emit('character:claim', { characterId }),
      release: (characterId) => socketRef.current?.emit('character:release', { characterId }),
      loadScript: (script) =>
        new Promise((resolve) => {
          const socket = socketRef.current;
          if (!socket) {
            resolve({ ok: false, error: 'Not connected.' });
            return;
          }
          socket.emit('script:load', { script }, resolve);
        }),
      setVoiceState: (inVoice, muted) =>
        socketRef.current?.emit('voice:state', { inVoice, muted }),
      sendSignal: (to, data) => socketRef.current?.emit('webrtc:signal', { to, data }),
      sendSpeechAttempt: (attempt) => socketRef.current?.emit('speech:attempt', attempt),
    }),
    []
  );

  const onSignal = useMemo(
    () => (handler: SignalHandler) => {
      signalHandlersRef.current.add(handler);
      return () => {
        signalHandlersRef.current.delete(handler);
      };
    },
    []
  );

  const onSpeechAttempt = useMemo(
    () => (handler: SpeechAttemptHandler) => {
      speechHandlersRef.current.add(handler);
      return () => {
        speechHandlersRef.current.delete(handler);
      };
    },
    []
  );

  const serverNow = useMemo(() => () => Date.now() + clockOffsetRef.current, []);

  return {
    connected,
    selfId,
    state,
    script,
    joinError,
    actions,
    onSignal,
    onSpeechAttempt,
    serverNow,
  };
}
