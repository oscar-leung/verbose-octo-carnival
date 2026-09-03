import { useMemo, useState } from 'react';
import { buildGrammarIndex, filterGrammarIndex } from '../lib/grammarIndex';
import { PUBLIC_SCENES } from '../data/demoScenes';

interface Props {
  onClose: () => void;
}

/**
 * 文法さくいん — every grammar pattern taught across the bundled scenes, in
 * one searchable list. Each pattern expands to the lines that teach it; an
 * occurrence links to its scene's public solo-practice page.
 */
export default function GrammarIndex({ onClose }: Props) {
  const index = useMemo(() => buildGrammarIndex(PUBLIC_SCENES), []);
  const [query, setQuery] = useState('');
  const [openPatterns, setOpenPatterns] = useState<Set<string>>(new Set());

  const shown = filterGrammarIndex(index, query);
  const toggle = (pattern: string) =>
    setOpenPatterns((prev) => {
      const next = new Set(prev);
      if (next.has(pattern)) next.delete(pattern);
      else next.add(pattern);
      return next;
    });

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal grammar-index" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>
            文法さくいん / grammar index ({index.length})
          </h2>
          <button className="chip" onClick={onClose}>
            ✕
          </button>
        </header>
        <input
          className="gi-search"
          type="search"
          placeholder="文法・意味で検索 / search patterns…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {shown.length === 0 ? (
          <p className="muted">見つかりません — no patterns match「{query}」.</p>
        ) : (
          <div className="gi-list">
            {shown.map((entry) => {
              const open = openPatterns.has(entry.pattern);
              return (
                <div key={entry.pattern} className="gi-entry">
                  <button
                    className={open ? 'gi-row open' : 'gi-row'}
                    onClick={() => toggle(entry.pattern)}
                    aria-expanded={open}
                  >
                    <span className="gi-pattern">{entry.pattern}</span>
                    <span className="gi-explanation">{entry.explanation}</span>
                    <span className="gi-count muted">
                      ×{entry.occurrences.length} {open ? '▾' : '▸'}
                    </span>
                  </button>
                  {open && (
                    <ul className="gi-occurrences">
                      {entry.occurrences.map((occ) => (
                        <li key={`${occ.scriptTitle}:${occ.lineId}`} className="gi-occurrence">
                          <span className="gi-line-jp">{occ.lineText}</span>
                          {occ.slug ? (
                            <a
                              className="chip gi-scene-link"
                              href={`#/p/${occ.slug}`}
                              title="この場面をソロ練習 / practice this scene solo"
                            >
                              {occ.scriptTitle.replace('葬送のフリーレン — ', '').replace('葬送のフリーレン ', '')}{' '}
                              →
                            </a>
                          ) : (
                            <span className="muted gi-scene-name">{occ.scriptTitle}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
