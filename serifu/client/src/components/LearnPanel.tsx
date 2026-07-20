import { useState } from 'react';
import type { ScriptLine } from '../../../shared/types';
import { addWord, hasWord } from '../lib/wordbook';

interface Props {
  line: ScriptLine;
  compact?: boolean;
  onWordAdded?: () => void;
}

/** Vocab + grammar notes for one line, with add-to-wordbook on each word. */
export default function LearnPanel({ line, compact, onWordAdded }: Props) {
  const [, bump] = useState(0);
  const vocab = line.vocab ?? [];
  const grammar = line.grammar ?? [];
  if (vocab.length === 0 && grammar.length === 0) {
    return compact ? null : <p className="muted learn-empty">No notes for this line (yet).</p>;
  }
  return (
    <div className={compact ? 'learn compact' : 'learn'}>
      {vocab.length > 0 && (
        <div className="learn-vocab">
          {vocab.map((v) => {
            const saved = hasWord(v.w);
            return (
              <span key={v.w} className="vocab-chip">
                <span className="vocab-jp">
                  {v.r ? (
                    <ruby>
                      {v.w}
                      <rt>{v.r}</rt>
                    </ruby>
                  ) : (
                    v.w
                  )}
                </span>
                <span className="vocab-en">{v.en}</span>
                <button
                  className="mini vocab-add"
                  title={saved ? 'in your wordbook' : 'save to 単語帳'}
                  disabled={saved}
                  onClick={() => {
                    addWord(v);
                    bump((n) => n + 1);
                    onWordAdded?.();
                  }}
                >
                  {saved ? '✓' : '＋'}
                </button>
              </span>
            );
          })}
        </div>
      )}
      {grammar.length > 0 && (
        <ul className="learn-grammar">
          {grammar.map((g) => (
            <li key={g.p}>
              <span className="grammar-p">{g.p}</span> — {g.en}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
