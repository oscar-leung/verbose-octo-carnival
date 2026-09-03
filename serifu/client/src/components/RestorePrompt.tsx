import type { RoomSnapshot } from '../lib/roomSnapshot';

interface Props {
  snapshot: RoomSnapshot;
  onAccept: () => void;
  onDecline: () => void;
}

/** Rough "how long ago", bilingual-lite (numbers speak for themselves). */
function agoLabel(savedAt: number, now: number): string {
  const mins = Math.max(1, Math.round((now - savedAt) / 60_000));
  if (mins < 60) return `${mins}分前 / ${mins}m ago`;
  const hours = Math.round(mins / 60);
  return `${hours}時間前 / ${hours}h ago`;
}

/**
 * One-tap offer to revive a room after a server restart wiped it: reloads
 * the snapshotted script + room settings and re-claims only YOUR previous
 * role. Friends get the same prompt on their own devices for theirs.
 */
export default function RestorePrompt({ snapshot, onAccept, onDecline }: Props) {
  return (
    <div className="restore-prompt" role="dialog" aria-label="前のセッションを復元 / restore previous session">
      <div className="restore-text">
        <strong>前のセッションを復元？ / restore previous session?</strong>
        <span className="muted">
          「{snapshot.script.title}」・{agoLabel(snapshot.savedAt, Date.now())}
        </span>
      </div>
      <button className="restore-accept" onClick={onAccept}>
        復元する <small>restore</small>
      </button>
      <button className="restore-decline" onClick={onDecline} title="keep the room empty">
        閉じる <small>dismiss</small>
      </button>
    </div>
  );
}
