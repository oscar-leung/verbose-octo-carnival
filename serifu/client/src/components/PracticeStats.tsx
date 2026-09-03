import type { RoomUser, UserStats } from '../../../shared/types';
import { buildRecapData, drawRecapCard } from '../lib/recapCard';

interface Props {
  users: RoomUser[];
  stats: Record<string, UserStats>;
  selfId: string;
}

/** Render the recap to an offscreen canvas and hand it over as a PNG download. */
function downloadRecap(users: RoomUser[], stats: Record<string, UserStats>, selfId: string) {
  const title = document.querySelector('.script-header h2')?.textContent ?? null;
  const canvas = document.createElement('canvas');
  drawRecapCard(canvas, buildRecapData(title, users, stats, selfId));
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'serifu-recap.png';
    a.click();
    URL.revokeObjectURL(url);
  }, 'image/png');
}

/** Live per-person practice tally — passes/attempts and average score. */
export default function PracticeStats({ users, stats, selfId }: Props) {
  const rows = users
    .map((u) => ({ user: u, s: stats[u.id] }))
    .filter((r): r is { user: RoomUser; s: UserStats } => !!r.s && r.s.attempts > 0);
  if (rows.length === 0) return null;
  const selfStats = stats[selfId];
  return (
    <div className="practice-stats">
      <span className="bar-label">成績</span>
      {rows.map(({ user, s }) => (
        <span
          key={user.id}
          className="stat-chip"
          style={{ borderColor: user.color }}
          title={`${s.attempts} attempts, ${s.passes} passed`}
        >
          {user.name}
          {user.id === selfId ? ' ★' : ''}: {s.passes}/{s.attempts} ·{' '}
          {Math.round(s.scoreSum / s.attempts)}%
        </span>
      ))}
      {selfStats && selfStats.attempts > 0 && (
        <button
          className="chip recap-btn"
          onClick={() => downloadRecap(users, stats, selfId)}
          title="save tonight's practice as a shareable image"
        >
          📸 きろく / recap
        </button>
      )}
    </div>
  );
}
