import { useMemo, useState } from 'react';
import {
  bandCounts,
  bandFor,
  dueEntries,
  gradeReview,
  loadMastery,
  type MasteryEntry,
} from '../lib/mastery';

interface Props {
  onClose: () => void;
  onChanged: () => void;
}

/**
 * Your mastery ledger: everything you've successfully spoken, banded
 * 新規 → 学習中 → 定着 → マスター, with a quick spaced-repetition review.
 */
export default function MasteryPanel({ onClose, onChanged }: Props) {
  const [entries, setEntries] = useState<MasteryEntry[]>(loadMastery);
  const [reviewQueue, setReviewQueue] = useState<MasteryEntry[] | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [sessionDone, setSessionDone] = useState(0);

  const now = Date.now();
  const due = useMemo(() => dueEntries(entries, now), [entries, now]);
  const counts = useMemo(() => bandCounts(entries), [entries]);

  const refresh = () => {
    setEntries(loadMastery());
    onChanged();
  };

  const startReview = () => {
    const queue = due.length > 0 ? due.slice(0, 20) : [...entries].sort(() => Math.random() - 0.5).slice(0, 10);
    setReviewQueue(queue);
    setSessionDone(0);
    setRevealed(false);
  };

  const grade = (correct: boolean) => {
    const current = reviewQueue?.[0];
    if (!current) return;
    gradeReview(current.key, correct);
    setSessionDone((n) => n + 1);
    setRevealed(false);
    setReviewQueue((q) => (q ? q.slice(1) : q));
    refresh();
  };

  const current = reviewQueue?.[0];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal mastery" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>習得 / mastery</h2>
          <button className="chip" onClick={onClose}>
            ✕
          </button>
        </header>

        {entries.length === 0 ? (
          <p className="muted">
            Nothing tracked yet — every vocab word and grammar pattern in a line you
            <strong> successfully speak</strong> lands here automatically. Go pass some lines! 🎤
          </p>
        ) : reviewQueue !== null ? (
          current ? (
            <div className="review-card">
              <div className="review-progress muted">
                {sessionDone + 1} / {sessionDone + reviewQueue.length} ·{' '}
                {current.kind === 'vocab' ? '単語' : '文法'}
              </div>
              <p className="review-front">
                {current.reading && revealed ? (
                  <ruby>
                    {current.front}
                    <rt>{current.reading}</rt>
                  </ruby>
                ) : (
                  current.front
                )}
              </p>
              {revealed ? (
                <>
                  <p className="review-back">{current.back}</p>
                  <div className="row">
                    <button className="primary" onClick={() => grade(true)}>
                      ○ knew it
                    </button>
                    <button onClick={() => grade(false)}>× missed it</button>
                  </div>
                </>
              ) : (
                <button className="primary" onClick={() => setRevealed(true)}>
                  show answer
                </button>
              )}
              <button className="chip end-review" onClick={() => setReviewQueue(null)}>
                end review
              </button>
            </div>
          ) : (
            <div className="review-card">
              <p>
                🎉 Review done — {sessionDone} item{sessionDone === 1 ? '' : 's'} graded.
              </p>
              <button className="primary" onClick={() => setReviewQueue(null)}>
                back to overview
              </button>
            </div>
          )
        ) : (
          <>
            <div className="mastery-bands">
              {(['新規', '学習中', '定着', 'マスター'] as const).map((band) => (
                <span key={band} className={`band-chip band-${band}`}>
                  {band} <strong>{counts[band]}</strong>
                </span>
              ))}
            </div>
            <div className="row">
              <button className="primary" onClick={startReview}>
                ▶ review {due.length > 0 ? `(${due.length} due)` : '(random 10)'}
              </button>
            </div>
            <div className="mastery-list">
              {[...entries]
                .sort((a, b) => b.addedAt - a.addedAt)
                .map((e) => (
                  <div key={e.key} className="mastery-row">
                    <span className={`band-dot band-${bandFor(e.level)}`} title={bandFor(e.level)} />
                    <span className="mastery-front">
                      {e.reading ? (
                        <ruby>
                          {e.front}
                          <rt>{e.reading}</rt>
                        </ruby>
                      ) : (
                        e.front
                      )}
                    </span>
                    <span className="mastery-back">{e.back}</span>
                    <span className="mastery-meta muted" title={`spoken ${e.seen}×, reviewed ${e.reviews}×`}>
                      🎤{e.seen} · Lv{e.level}
                    </span>
                  </div>
                ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
