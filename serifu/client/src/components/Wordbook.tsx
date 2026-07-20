import { useState } from 'react';
import {
  clearWordbook,
  loadWordbook,
  removeWord,
  wordbookToCsv,
  type WordEntry,
} from '../lib/wordbook';

interface Props {
  onClose: () => void;
  onChanged: () => void;
}

/** The personal word list collected while practicing, with CSV export. */
export default function Wordbook({ onClose, onChanged }: Props) {
  const [entries, setEntries] = useState<WordEntry[]>(loadWordbook);

  const refresh = () => {
    setEntries(loadWordbook());
    onChanged();
  };

  const exportCsv = () => {
    const blob = new Blob([wordbookToCsv(entries)], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'serifu-wordbook.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal wordbook" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>単語帳 / my wordbook ({entries.length})</h2>
          <button className="chip" onClick={onClose}>
            ✕
          </button>
        </header>
        {entries.length === 0 ? (
          <p className="muted">
            Empty so far — open a line's 学 panel in the script and tap ＋ on any word to save it
            here while you practice.
          </p>
        ) : (
          <>
            <div className="word-list">
              {entries.map((e) => (
                <div key={e.w} className="word-row">
                  <span className="word-jp">
                    {e.r ? (
                      <ruby>
                        {e.w}
                        <rt>{e.r}</rt>
                      </ruby>
                    ) : (
                      e.w
                    )}
                  </span>
                  <span className="word-en">{e.en}</span>
                  <button
                    className="mini"
                    title="remove"
                    onClick={() => {
                      removeWord(e.w);
                      refresh();
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
            <footer className="modal-footer">
              <button
                onClick={() => {
                  clearWordbook();
                  refresh();
                }}
              >
                clear all
              </button>
              <div className="spacer" />
              <button className="primary" onClick={exportCsv}>
                ⬇ export CSV (Anki-ready)
              </button>
            </footer>
          </>
        )}
      </div>
    </div>
  );
}
