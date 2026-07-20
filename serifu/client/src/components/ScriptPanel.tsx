import { useEffect, useRef, useState, type CSSProperties } from 'react';
import type { RoomUser, SkitScript } from '../../../shared/types';
import type { DisplaySettings } from '../lib/settings';
import { formatTime } from '../lib/playback';
import RubyText from './RubyText';
import LearnPanel from './LearnPanel';

interface Props {
  script: SkitScript | null;
  activeLineId: string | null;
  claims: Record<string, string>;
  users: RoomUser[];
  selfId: string;
  settings: DisplaySettings;
  onSeekLine: (start: number) => void;
  onOpenEditor: () => void;
  onLoadDemo: () => void;
  onWordAdded: () => void;
}

export default function ScriptPanel({
  script,
  activeLineId,
  claims,
  users,
  selfId,
  settings,
  onSeekLine,
  onOpenEditor,
  onLoadDemo,
  onWordAdded,
}: Props) {
  const listRef = useRef<HTMLDivElement | null>(null);
  const [follow, setFollow] = useState(true);
  const [openLearn, setOpenLearn] = useState<Set<string>>(new Set());

  const toggleLearn = (lineId: string) => {
    setOpenLearn((prev) => {
      const next = new Set(prev);
      if (next.has(lineId)) next.delete(lineId);
      else next.add(lineId);
      return next;
    });
  };

  // Manual wheel/touch scrolling turns auto-follow off until re-enabled.
  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    const stopFollowing = () => setFollow(false);
    el.addEventListener('wheel', stopFollowing, { passive: true });
    el.addEventListener('touchmove', stopFollowing, { passive: true });
    return () => {
      el.removeEventListener('wheel', stopFollowing);
      el.removeEventListener('touchmove', stopFollowing);
    };
  }, [script]);

  useEffect(() => {
    if (!follow || !activeLineId || !listRef.current) return;
    const el = listRef.current.querySelector(`[data-line-id="${activeLineId}"]`);
    el?.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, [activeLineId, follow]);

  if (!script) {
    return (
      <div className="script-panel empty">
        <p>まだ台本がないよ — no script loaded yet.</p>
        <div className="row">
          <button className="primary" onClick={onLoadDemo}>
            デモ台本を読み込む / load demo scene
          </button>
          <button onClick={onOpenEditor}>字幕をインポート / import subtitles</button>
        </div>
      </div>
    );
  }

  const charById = new Map(script.characters.map((c) => [c.id, c]));
  const userById = new Map(users.map((u) => [u.id, u]));

  return (
    <div className="script-panel">
      <div className="script-header">
        <h2 title={script.title}>{script.title}</h2>
        {!follow && (
          <button className="chip" onClick={() => setFollow(true)}>
            ⤓ follow
          </button>
        )}
      </div>
      <div className="line-list" ref={listRef}>
        {script.lines.map((line) => {
          const char = line.character !== null ? charById.get(line.character) : undefined;
          const ownerId = line.character !== null ? claims[line.character] : undefined;
          const owner = ownerId !== undefined ? userById.get(ownerId) : undefined;
          const mine = ownerId === selfId;
          const classes = [
            'line',
            line.id === activeLineId ? 'active' : '',
            mine ? 'mine' : '',
          ]
            .filter(Boolean)
            .join(' ');
          const style = { '--char-color': char?.color ?? '#556' } as CSSProperties;
          return (
            <div key={line.id} data-line-id={line.id} className={classes} style={style}>
              <button
                className="line-time"
                onClick={() => onSeekLine(line.start)}
                title="jump here"
              >
                {formatTime(line.start)}
              </button>
              <div className="line-body">
                <div className="line-meta">
                  <span className="char-name" style={{ color: char?.color }}>
                    {char?.name ?? '—'}
                  </span>
                  {owner && (
                    <span className="owner-name">
                      🎤 {owner.name}
                      {mine ? ' (you)' : ''}
                    </span>
                  )}
                  {owner && (
                    <button
                      className="mini replay"
                      title="practice this line again"
                      onClick={() => onSeekLine(Math.max(0, line.start - 0.3))}
                    >
                      🔁
                    </button>
                  )}
                  {(line.vocab?.length || line.grammar?.length) ? (
                    <button
                      className={openLearn.has(line.id) ? 'mini learn-toggle open' : 'mini learn-toggle'}
                      title="vocab & grammar for this line"
                      onClick={() => toggleLearn(line.id)}
                    >
                      学
                    </button>
                  ) : null}
                </div>
                <div className="line-text">
                  <RubyText tokens={line.tokens} furigana={settings.furigana} />
                </div>
                {line.translation && settings.translation !== 'hide' && (
                  <div
                    className={
                      settings.translation === 'hover'
                        ? 'line-translation hover-reveal'
                        : 'line-translation'
                    }
                  >
                    {line.translation}
                  </div>
                )}
                {openLearn.has(line.id) && (
                  <LearnPanel line={line} onWordAdded={onWordAdded} />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
