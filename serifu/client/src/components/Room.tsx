import { useEffect, useMemo, useRef, useState } from 'react';
import { useRoom } from '../lib/useRoom';
import { expectedPosition, findActiveLineId } from '../lib/playback';
import { loadSettings, saveSettings, type DisplaySettings } from '../lib/settings';
import VideoPanel from './VideoPanel';
import ScriptPanel from './ScriptPanel';
import CharacterBar, { STRICTNESS_PRESETS } from './CharacterBar';
import RehearsalBanner from './RehearsalBanner';
import VoicePanel from './VoicePanel';
import PracticeStats from './PracticeStats';
import BgmPlayer from './BgmPlayer';
import ScriptEditor from './ScriptEditor';
import Wordbook from './Wordbook';
import EpisodeBrowser from './EpisodeBrowser';
import MasteryPanel from './MasteryPanel';
import GrammarIndex from './GrammarIndex';
import { loadWordbook } from '../lib/wordbook';
import { dueEntries, loadMastery } from '../lib/mastery';
import {
  buildRoomSnapshot,
  isSnapshotFresh,
  loadRoomSnapshot,
  ownClaimedCharacterIds,
  saveRoomSnapshot,
  type RoomSnapshot,
} from '../lib/roomSnapshot';
import RestorePrompt from './RestorePrompt';
import type { SkitScript } from '../../../shared/types';

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
  const [editorInitial, setEditorInitial] = useState<SkitScript | null>(null);
  const [episodesOpen, setEpisodesOpen] = useState(false);
  const [wordbookOpen, setWordbookOpen] = useState(false);
  const [masteryOpen, setMasteryOpen] = useState(false);
  const [grammarOpen, setGrammarOpen] = useState(false);
  const [masteryDue, setMasteryDue] = useState(() => dueEntries(loadMastery(), Date.now()).length);
  const refreshMastery = () => setMasteryDue(dueEntries(loadMastery(), Date.now()).length);
  /** Phone layout: which of the three tabs is showing (no effect on desktop). */
  const [mobileTab, setMobileTab] = useState<'stage' | 'script' | 'more'>('stage');
  const pausedForLine = state?.playback.pausedForLineId;
  useEffect(() => {
    // The rehearsal moment always brings the stage forward on phones.
    if (pausedForLine) setMobileTab('stage');
  }, [pausedForLine]);
  const [wordCount, setWordCount] = useState(() => loadWordbook().length);
  const [copied, setCopied] = useState(false);
  const [position, setPosition] = useState(0);
  const videoPosRef = useRef<number | null>(null);
  /** Snapshot offered for one-tap restore after a server restart wiped the room. */
  const [restoreSnap, setRestoreSnap] = useState<RoomSnapshot | null>(null);
  const [restoreDismissed, setRestoreDismissed] = useState(false);

  // Keep a per-room localStorage snapshot of what matters (script, claims by
  // name, rehearsal settings) so a free-tier server restart isn't fatal.
  // The signature keeps the (potentially large) script serialization off the
  // hot path — room:state broadcasts arrive on every playback event.
  const snapSig = useMemo(() => {
    if (!script || !state || state.scriptVersion === 0) return null;
    return JSON.stringify([
      state.scriptVersion,
      state.claims,
      state.passScore,
      state.rehearsalEnabled,
      state.users.map((u) => [u.id, u.name]),
    ]);
  }, [script, state]);
  useEffect(() => {
    if (!snapSig || !script || !state) return;
    // Guard against hash navigation between rooms: for one render the OLD
    // room's script/state can coexist with the NEW roomId prop — never save
    // one room's session under another room's key.
    if (state.roomId !== roomId) return;
    saveRoomSnapshot(roomId, buildRoomSnapshot(script, state, Date.now()));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [snapSig, roomId]);

  // Entering a different room resets the offer state.
  useEffect(() => {
    setRestoreSnap(null);
    setRestoreDismissed(false);
  }, [roomId]);

  // On (re)join: if the server room has no script but we hold a fresh
  // snapshot for this roomId, offer to restore. If someone else loads a
  // script first (their own restore, or a fresh one), the offer withdraws.
  const scriptVersion = state?.scriptVersion;
  useEffect(() => {
    if (scriptVersion === undefined) return;
    if (scriptVersion > 0) {
      setRestoreSnap(null);
      return;
    }
    if (restoreDismissed) return;
    const snap = loadRoomSnapshot(roomId);
    if (snap && isSnapshotFresh(snap, Date.now())) setRestoreSnap(snap);
  }, [scriptVersion, roomId, restoreDismissed]);

  const selfName = state?.users.find((u) => u.id === selfId)?.name ?? name;
  const acceptRestore = async () => {
    const snap = restoreSnap;
    if (!snap) return;
    setRestoreSnap(null);
    setRestoreDismissed(true);
    const r = await actions.loadScript(snap.script);
    if (!r.ok) return; // server refused (e.g. stale/oversized) — leave the room as-is
    actions.setRehearsal(snap.rehearsalEnabled);
    actions.setPassScore(snap.passScore);
    // Re-claim only OUR previous role(s), matched by character name; the
    // others re-claim theirs when they accept their own prompts.
    for (const charId of ownClaimedCharacterIds(snap, selfName)) {
      actions.claim(charId);
    }
  };

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
        <button onClick={() => setEpisodesOpen(true)} title="season & episode tracker">
          話数 <small>episodes</small>
        </button>
        <button onClick={() => setMasteryOpen(true)} title="grammar & vocab mastery tracker">
          習得 {masteryDue > 0 ? `(${masteryDue})` : ''} <small>mastery</small>
        </button>
        <button onClick={() => setWordbookOpen(true)} title="your saved words">
          単語帳 {wordCount > 0 ? `(${wordCount})` : ''} <small>wordbook</small>
        </button>
        <button onClick={() => setGrammarOpen(true)} title="browse every grammar pattern taught">
          文法 <small>grammar</small>
        </button>
        <button
          onClick={() => {
            setEditorInitial(null);
            setEditorOpen(true);
          }}
        >
          台本 ✎ <small>edit script</small>
        </button>
      </header>

      {restoreSnap && (
        <RestorePrompt
          snapshot={restoreSnap}
          onAccept={() => void acceptRestore()}
          onDecline={() => {
            // Dismiss for this visit only; the snapshot itself is kept.
            setRestoreSnap(null);
            setRestoreDismissed(true);
          }}
        />
      )}

      <div className={`room-grid mtab-${mobileTab}`}>
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
              onShowScript={() => setMobileTab('script')}
            />
            {state.playback.pausedForLineId && script && (
              <RehearsalBanner
                script={script}
                state={state}
                selfId={selfId}
                actions={actions}
                settings={settings}
                onSpeechAttempt={onSpeechAttempt}
                onMasteryChanged={refreshMastery}
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
          <div className="more-actions">
            <button onClick={() => setEpisodesOpen(true)}>
              話数 <small>episodes</small>
            </button>
            <button onClick={() => setMasteryOpen(true)}>
              習得 {masteryDue > 0 ? `(${masteryDue})` : ''} <small>mastery</small>
            </button>
            <button onClick={() => setWordbookOpen(true)}>
              単語帳 {wordCount > 0 ? `(${wordCount})` : ''} <small>wordbook</small>
            </button>
            <button onClick={() => setGrammarOpen(true)}>
              文法 <small>grammar</small>
            </button>
            <button
              onClick={() => {
                setEditorInitial(null);
                setEditorOpen(true);
              }}
            >
              台本 ✎ <small>edit script</small>
            </button>
          </div>
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
                <option value="show">表示 / show</option>
                <option value="hover">タップ / tap</option>
                <option value="hide">隠す / hide</option>
              </select>
            </label>
            {/* Room-level rehearsal settings live here on phones (audit-01
                finding 5); desktop keeps them in the character bar. */}
            <label
              className="toggle mobile-room-setting"
              title="Auto-pause the video at the start of every claimed line so its actor can say it first."
            >
              <input
                type="checkbox"
                checked={state.rehearsalEnabled}
                onChange={(e) => actions.setRehearsal(e.target.checked)}
              />
              セリフで自動停止
            </label>
            <label
              className="toggle mobile-room-setting"
              title="Speech score needed to pass and auto-resume — shared by the whole room."
            >
              判定
              <select
                value={state.passScore}
                onChange={(e) => actions.setPassScore(Number(e.target.value))}
              >
                {STRICTNESS_PRESETS.map((p) => (
                  <option key={p.score} value={p.score}>
                    {p.label}
                  </option>
                ))}
                {!STRICTNESS_PRESETS.some((p) => p.score === state.passScore) && (
                  <option value={state.passScore}>{state.passScore}+</option>
                )}
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

      <nav className="mobile-nav" aria-label="sections">
        {(
          [
            ['stage', '🎬', 'ステージ'],
            ['script', '📖', '台本'],
            ['more', '⚙️', 'その他'],
          ] as const
        ).map(([tab, icon, label]) => (
          <button
            key={tab}
            className={mobileTab === tab ? 'mnav-btn current' : 'mnav-btn'}
            onClick={() => setMobileTab(tab)}
          >
            <span className="mnav-icon">{icon}</span>
            {label}
          </button>
        ))}
      </nav>

      {editorOpen && (
        <ScriptEditor
          script={script}
          initialScript={editorInitial}
          actions={actions}
          onClose={() => {
            setEditorOpen(false);
            setEditorInitial(null);
          }}
        />
      )}
      {episodesOpen && (
        <EpisodeBrowser
          currentScript={script}
          onLoadScript={(s) => void actions.loadScript(s)}
          onPrepEpisode={(suggestedTitle) => {
            setEpisodesOpen(false);
            setEditorInitial({ title: suggestedTitle, characters: [], lines: [] });
            setEditorOpen(true);
          }}
          onClose={() => setEpisodesOpen(false)}
        />
      )}
      {wordbookOpen && (
        <Wordbook
          onClose={() => setWordbookOpen(false)}
          onChanged={() => setWordCount(loadWordbook().length)}
        />
      )}
      {grammarOpen && <GrammarIndex onClose={() => setGrammarOpen(false)} />}
      {masteryOpen && (
        <MasteryPanel
          onClose={() => {
            setMasteryOpen(false);
            refreshMastery();
          }}
          onChanged={refreshMastery}
        />
      )}
    </div>
  );
}
