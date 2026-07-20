import { useEffect, useMemo, useRef, useState } from 'react';
import { useRoom } from '../lib/useRoom';
import { expectedPosition, findActiveLineId } from '../lib/playback';
import { loadSettings, saveSettings, type DisplaySettings } from '../lib/settings';
import VideoPanel from './VideoPanel';
import ScriptPanel from './ScriptPanel';
import CharacterBar from './CharacterBar';
import RehearsalBanner from './RehearsalBanner';
import VoicePanel from './VoicePanel';
import PracticeStats from './PracticeStats';
import BgmPlayer from './BgmPlayer';
import ScriptEditor from './ScriptEditor';
import Wordbook from './Wordbook';
import { loadWordbook } from '../lib/wordbook';

export default function Room({ roomId, name }: { roomId: string; name: string }) {
  const {
    connected,
    selfId,
    state,
    script,
    joinError,
    actions,
    onSignal,
    onSpeechAttempt,
    serverNow,
  } = useRoom(roomId, name);
  const [settings, setSettings] = useState<DisplaySettings>(loadSettings);
  const [userOffset, setUserOffset] = useState(0);
  const [editorOpen, setEditorOpen] = useState(false);
  const [wordbookOpen, setWordbookOpen] = useState(false);
  const [wordCount, setWordCount] = useState(() => loadWordbook().length);
  const [copied, setCopied] = useState(false);
  const [position, setPosition] = useState(0);
  const videoPosRef = useRef<number | null>(null);

  const updateSettings = (next: DisplaySettings) => {
    setSettings(next);
    saveSettings(next);
  };

  // Ticking room position: prefer the local video's clock, else extrapolate
  // from the last server playback state.
  useEffect(() => {
    const timer = setInterval(() => {
      const pos =
        videoPosRef.current ?? (state ? expectedPosition(state.playback, serverNow()) : 0);
      setPosition(Math.round(pos * 10) / 10);
    }, 250);
    return () => clearInterval(timer);
  }, [state, serverNow]);

  const activeLineId = useMemo(
    () => (script ? findActiveLineId(script.lines, position) : null),
    [script, position]
  );

  // Global shortcuts: space/k toggle, arrows seek. Ignored while typing.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.tagName === 'SELECT' ||
          target.isContentEditable)
      ) {
        return;
      }
      if (!state || editorOpen) return;
      const pos = videoPosRef.current ?? expectedPosition(state.playback, serverNow());
      if (e.key === ' ' || e.key === 'k') {
        e.preventDefault();
        if (state.playback.pausedForLineId) actions.rehearsalResume();
        else if (state.playback.isPlaying) actions.pause(pos);
        else actions.play(pos);
      } else if (e.key === 'ArrowLeft' || e.key === 'j') {
        e.preventDefault();
        actions.seek(Math.max(0, pos - 5));
      } else if (e.key === 'ArrowRight' || e.key === 'l') {
        e.preventDefault();
        actions.seek(pos + 5);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [state, actions, serverNow, editorOpen]);

  const copyLink = () => {
    navigator.clipboard
      .writeText(location.href)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      })
      .catch(() => {
        // Clipboard can fail on http:// origins; the URL bar still works.
      });
  };

  if (joinError) {
    return (
      <div className="landing">
        <div className="landing-card">
          <h1 className="logo">
            Serifu <span className="logo-jp">台詞</span>
          </h1>
          <p className="error">{joinError}</p>
          <a href="#/">← back to start</a>
        </div>
      </div>
    );
  }

  if (!state || !selfId) {
    return (
      <div className="landing">
        <div className="landing-card">
          <p>{connected ? 'joining room…' : 'connecting…'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="room">
      <header className="room-header">
        <a className="logo small" href="#/">
          Serifu <span className="logo-jp">台詞</span>
        </a>
        <button className="chip" onClick={copyLink} title="copy invite link">
          {copied ? '✓ link copied' : `room ${roomId} ⧉`}
        </button>
        <span
          className={connected ? 'conn-dot on' : 'conn-dot off'}
          title={connected ? 'connected' : 'reconnecting…'}
        />
        <div className="spacer" />
        <div className="user-chips">
          {state.users.map((u) => (
            <span className="chip user" key={u.id} style={{ borderColor: u.color }}>
              {u.inVoice ? (u.muted ? '🔇 ' : '🎙 ') : ''}
              {u.name}
              {u.id === selfId ? ' ★' : ''}
            </span>
          ))}
        </div>
        <button onClick={() => setWordbookOpen(true)} title="your saved words">
          単語帳 {wordCount > 0 ? `(${wordCount})` : ''}
        </button>
        <button onClick={() => setEditorOpen(true)}>台本 ✎</button>
      </header>

      <div className="room-grid">
        <section className="stage">
          <div className="video-wrap">
            <VideoPanel
              playback={state.playback}
              script={script}
              claims={state.claims}
              rehearsalEnabled={state.rehearsalEnabled}
              actions={actions}
              serverNow={serverNow}
              userOffset={userOffset}
              videoPosRef={videoPosRef}
            />
            {state.playback.pausedForLineId && script && (
              <RehearsalBanner
                script={script}
                state={state}
                selfId={selfId}
                actions={actions}
                settings={settings}
                onSpeechAttempt={onSpeechAttempt}
              />
            )}
          </div>
          <VoicePanel selfId={selfId} users={state.users} actions={actions} onSignal={onSignal} />
          <CharacterBar
            script={script}
            claims={state.claims}
            users={state.users}
            selfId={selfId}
            rehearsalEnabled={state.rehearsalEnabled}
            passScore={state.passScore}
            actions={actions}
            onOpenEditor={() => setEditorOpen(true)}
          />
          <PracticeStats users={state.users} stats={state.stats} selfId={selfId} />
          <BgmPlayer />
        </section>

        <aside className="side">
          {script?.scenes && script.scenes.length > 0 && (
            <div className="scene-bar">
              <span className="bar-label">名場面</span>
              {script.scenes.map((sc) => (
                <button
                  key={sc.id}
                  className={
                    position >= sc.start && position < sc.end ? 'chip scene current' : 'chip scene'
                  }
                  onClick={() => actions.seek(sc.start)}
                  title={`jump to ${sc.title}`}
                >
                  {sc.title}
                </button>
              ))}
            </div>
          )}
          <div className="settings-row">
            <label className="toggle">
              <input
                type="checkbox"
                checked={settings.furigana}
                onChange={(e) => updateSettings({ ...settings, furigana: e.target.checked })}
              />
              ふりがな
            </label>
            <label className="toggle">
              訳
              <select
                value={settings.translation}
                onChange={(e) =>
                  updateSettings({
                    ...settings,
                    translation: e.target.value as DisplaySettings['translation'],
                  })
                }
              >
                <option value="show">show</option>
                <option value="hover">on hover</option>
                <option value="hide">hide</option>
              </select>
            </label>
            <label className="toggle offset" title="Shift your local video vs. the room (for different encodes/cuts)">
              my offset
              <button onClick={() => setUserOffset((o) => Math.round((o - 0.5) * 10) / 10)}>−</button>
              <span className="offset-value">{userOffset.toFixed(1)}s</span>
              <button onClick={() => setUserOffset((o) => Math.round((o + 0.5) * 10) / 10)}>＋</button>
            </label>
          </div>
          <ScriptPanel
            script={script}
            activeLineId={activeLineId}
            claims={state.claims}
            users={state.users}
            selfId={selfId}
            settings={settings}
            onSeekLine={(start) => actions.seek(start)}
            onOpenEditor={() => setEditorOpen(true)}
            onLoadScript={(s) => void actions.loadScript(s)}
            onWordAdded={() => setWordCount(loadWordbook().length)}
          />
        </aside>
      </div>

      {editorOpen && (
        <ScriptEditor script={script} actions={actions} onClose={() => setEditorOpen(false)} />
      )}
      {wordbookOpen && (
        <Wordbook
          onClose={() => setWordbookOpen(false)}
          onChanged={() => setWordCount(loadWordbook().length)}
        />
      )}
    </div>
  );
}
