import { useEffect, useRef, useState } from 'react';
import type { RoomState, SkitScript } from '../../../shared/types';
import type { RoomActions, SpeechAttemptEvent, SpeechAttemptHandler } from '../lib/useRoom';
import type { DisplaySettings } from '../lib/settings';
import { scoreAttempt, SpeechListener, speechSupported } from '../lib/speech';
import RubyText from './RubyText';

interface Props {
  script: SkitScript;
  state: RoomState;
  selfId: string;
  actions: RoomActions;
  settings: DisplaySettings;
  onSpeechAttempt: (handler: SpeechAttemptHandler) => () => void;
}

/**
 * Overlay shown while playback is auto-paused for someone to act a line.
 * If it's YOUR line and the browser supports Japanese speech recognition,
 * we listen live, score the attempt against the script, and auto-resume
 * the anime when you nail it. Everyone else sees your attempts as they land.
 */
export default function RehearsalBanner({
  script,
  state,
  selfId,
  actions,
  settings,
  onSpeechAttempt,
}: Props) {
  const lineId = state.playback.pausedForLineId;
  const line = script.lines.find((l) => l.id === lineId);
  const char = line ? script.characters.find((c) => c.id === line.character) : undefined;
  const ownerId = line && line.character !== null ? state.claims[line.character] : undefined;
  const owner = state.users.find((u) => u.id === ownerId);
  const isMine = ownerId !== undefined && ownerId === selfId;

  const listenerRef = useRef<SpeechListener | null>(null);
  const passedRef = useRef(false);
  // Ref so mid-line threshold changes apply without restarting the mic.
  const passScoreRef = useRef(state.passScore);
  passScoreRef.current = state.passScore;
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState('');
  const [lastScore, setLastScore] = useState<number | null>(null);
  const [lastTranscript, setLastTranscript] = useState('');
  const [passed, setPassed] = useState(false);
  const [speechError, setSpeechError] = useState<string | null>(null);
  const [peerAttempt, setPeerAttempt] = useState<SpeechAttemptEvent | null>(null);

  // Start/stop the microphone with the banner's lifecycle (owner only).
  useEffect(() => {
    passedRef.current = false;
    setListening(false);
    setInterim('');
    setLastScore(null);
    setLastTranscript('');
    setPassed(false);
    setSpeechError(null);
    setPeerAttempt(null);
    if (!line || !isMine) return;
    if (!speechSupported()) {
      setSpeechError('unsupported');
      return;
    }
    const listener = new SpeechListener();
    listenerRef.current = listener;
    const ok = listener.start({
      onInterim: (text) => setInterim(text),
      onFinal: (text) => {
        if (passedRef.current) return;
        const score = scoreAttempt(text, line);
        const didPass = score >= passScoreRef.current;
        setInterim('');
        setLastTranscript(text);
        setLastScore(score);
        actions.sendSpeechAttempt({ lineId: line.id, transcript: text, score, passed: didPass });
        if (didPass) {
          passedRef.current = true;
          setPassed(true);
          listener.stop();
          // A short beat so the actor sees their score before the anime rolls.
          setTimeout(() => actions.rehearsalResume(), 700);
        }
      },
      onError: (message) => setSpeechError(message),
    });
    setListening(ok);
    return () => {
      listener.stop();
      listenerRef.current = null;
    };
  }, [line?.id, isMine]); // eslint-disable-line react-hooks/exhaustive-deps

  // Watch everyone's attempts for this line (including confirming our own).
  useEffect(() => {
    if (!line) return;
    return onSpeechAttempt((attempt) => {
      if (attempt.lineId !== line.id) return;
      if (attempt.userId !== selfId) setPeerAttempt(attempt);
    });
  }, [line?.id, selfId, onSpeechAttempt]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!line) return null;

  return (
    <div className="rehearsal-banner">
      <div className="rb-header">
        🎬 <strong style={{ color: char?.color }}>{char?.name ?? '???'}</strong>
        {owner ? (
          <span>
            {' '}
            — {isMine ? 'your line! 言ってみて！' : `${owner.name}'s line — listen for it!`}
          </span>
        ) : null}
      </div>
      <p className="rb-line">
        <RubyText tokens={line.tokens} furigana={settings.furigana} />
      </p>
      {line.translation && settings.translation !== 'hide' && (
        <p
          className={
            settings.translation === 'hover' ? 'rb-translation hover-reveal' : 'rb-translation'
          }
        >
          {line.translation}
        </p>
      )}

      {isMine && (
        <div className="speech-zone">
          {passed ? (
            <div className="score-badge pass">
              🎉 {lastScore}% — 合格！ rolling…
            </div>
          ) : listening ? (
            <div className="speech-status">
              <span className="mic-live">🎤 listening… (判定 {state.passScore}+)</span>
              {interim && <span className="speech-interim">「{interim}」</span>}
              {lastScore !== null && (
                <span className="score-badge fail">
                  {lastScore}% — もう一回！ <small>「{lastTranscript}」</small>
                </span>
              )}
            </div>
          ) : speechError === 'unsupported' ? (
            <div className="speech-status muted">
              Speech scoring needs Chrome/Edge — read the line aloud, then continue.
            </div>
          ) : speechError ? (
            <div className="speech-status muted">
              mic hiccup ({speechError}) — read it aloud and continue.
            </div>
          ) : null}
        </div>
      )}

      {!isMine && peerAttempt && (
        <div className={peerAttempt.passed ? 'peer-attempt pass' : 'peer-attempt'}>
          {peerAttempt.userName}: {peerAttempt.score}%{' '}
          {peerAttempt.passed ? '✓ 合格' : '… trying again'}
          {peerAttempt.transcript && <small> 「{peerAttempt.transcript}」</small>}
        </div>
      )}

      <button className="primary" onClick={() => actions.rehearsalResume()}>
        {isMine && listening ? 'skip scoring — continue ▶' : '続ける ▶'} <small>(space)</small>
      </button>
    </div>
  );
}
