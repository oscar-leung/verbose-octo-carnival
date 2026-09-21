import { useState } from 'react';
import type { SkitScript } from '../../../shared/types';
import {
  episodeKey,
  loadCounts,
  loadEpisodes,
  saveCount,
  saveEpisode,
  scriptForEpisode,
  SEASONS,
  type EpisodeMeta,
} from '../lib/episodes';
import { loadLibrary } from '../lib/scriptLibrary';

interface Props {
  currentScript: SkitScript | null;
  onLoadScript: (script: SkitScript) => void;
  onPrepEpisode: (suggestedTitle: string) => void;
  onClose: () => void;
}

/**
 * The whole journey at a glance: every episode of both seasons as a slot.
 * Import an episode's subtitles once, save it to the library, link it here —
 * then any session is one click from any episode.
 */
export default function EpisodeBrowser({ currentScript, onLoadScript, onPrepEpisode, onClose }: Props) {
  const [episodes, setEpisodes] = useState(loadEpisodes);
  const [counts, setCounts] = useState(loadCounts);
  const libraryTitles = new Set(loadLibrary().map((e) => e.title));
  // Later seasons stay folded until one of their episodes is prepped —
  // first-time users see one season, not a wall of empty slots
  // (audit-02 finding 2).
  const [openSeasons, setOpenSeasons] = useState<Record<number, boolean>>(() => {
    const eps = loadEpisodes();
    const lib = new Set(loadLibrary().map((e) => e.title));
    return Object.fromEntries(
      SEASONS.map((s) => [
        s.n,
        s.n === SEASONS[0]?.n ||
          Object.entries(eps).some(
            ([key, m]) =>
              key.startsWith(`s${s.n}e`) && m.scriptTitle !== undefined && lib.has(m.scriptTitle)
          ),
      ])
    );
  });

  const update = (key: string, meta: EpisodeMeta) => {
    setEpisodes(saveEpisode(key, meta));
  };

  const prepped = Object.values(episodes).filter(
    (m) => m.scriptTitle && libraryTitles.has(m.scriptTitle)
  ).length;
  const practiced = Object.values(episodes).filter((m) => m.practiced).length;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal episodes" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>話数 / episodes</h2>
          <button className="chip" onClick={onClose}>
            ✕
          </button>
        </header>
        <p className="muted episodes-count">
          {prepped} prepped · {practiced} practiced
        </p>
        <p className="muted episodes-hint">
          字幕を取り込んで各話を準備してね — import an episode's subs to prep it (README →
          jimaku.cc).
        </p>
        <div className="episodes-list">
          {SEASONS.map((season) => (
            <section key={season.n}>
              <button
                className="season-label"
                aria-expanded={openSeasons[season.n] ?? false}
                onClick={() =>
                  setOpenSeasons((prev) => ({ ...prev, [season.n]: !prev[season.n] }))
                }
              >
                {openSeasons[season.n] ? '▾' : '▸'} {season.label}
              </button>
              {(openSeasons[season.n] ?? false) &&
                Array.from({ length: counts[season.n] ?? season.defaultCount }, (_, i) => {
                const ep = i + 1;
                const key = episodeKey(season.n, ep);
                const meta = episodes[key] ?? { title: '' };
                const linked = meta.scriptTitle !== undefined && libraryTitles.has(meta.scriptTitle);
                const suggested = `葬送のフリーレン S${season.n}E${ep}`;
                return (
                  <div key={key} className={linked ? 'episode-row prepped' : 'episode-row'}>
                    <span className="ep-num">
                      S{season.n}E{ep}
                    </span>
                    <input
                      className="ep-title"
                      value={meta.title}
                      placeholder="タイトル / title"
                      onChange={(e) => update(key, { ...meta, title: e.target.value })}
                    />
                    <span className={linked ? 'ep-status ok' : 'ep-status'}>
                      {linked ? '台本あり' : '未準備'}
                    </span>
                    {linked ? (
                      <button
                        className="mini"
                        title="load this episode's script into the room"
                        onClick={() => {
                          const s = scriptForEpisode(meta);
                          if (s) {
                            onLoadScript(s);
                            onClose();
                          }
                        }}
                      >
                        ▶
                      </button>
                    ) : (
                      <button
                        className="mini"
                        title="prep this episode: import its subtitles in the editor"
                        onClick={() => onPrepEpisode(meta.title || suggested)}
                      >
                        ✎
                      </button>
                    )}
                    <button
                      className="mini"
                      title="link the room's current script to this episode (save it to the library first)"
                      disabled={!currentScript}
                      onClick={() => {
                        if (currentScript) {
                          update(key, {
                            ...meta,
                            title: meta.title || currentScript.title,
                            scriptTitle: currentScript.title,
                          });
                        }
                      }}
                    >
                      ⤓
                    </button>
                    <label className="toggle ep-practiced" title="mark as practiced">
                      <input
                        type="checkbox"
                        checked={meta.practiced ?? false}
                        onChange={(e) => update(key, { ...meta, practiced: e.target.checked })}
                      />
                      ✓
                    </label>
                  </div>
                );
              })}
              {season.airing && (openSeasons[season.n] ?? false) && (
                <button
                  className="mini add-episode"
                  onClick={() => {
                    const next = (counts[season.n] ?? season.defaultCount) + 1;
                    saveCount(season.n, next);
                    setCounts(loadCounts());
                  }}
                >
                  ＋ add episode (as they air)
                </button>
              )}
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
