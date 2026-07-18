import type { RoomUser, UserStats } from '../../../shared/types';

interface Props {
  users: RoomUser[];
  stats: Record<string, UserStats>;
  selfId: string;
}

/** Live per-person practice tally — passes/attempts and average score. */
export default function PracticeStats({ users, stats, selfId }: Props) {
  const rows = users
    .map((u) => ({ user: u, s: stats[u.id] }))
    .filter((r): r is { user: RoomUser; s: UserStats } => !!r.s && r.s.attempts > 0);
  if (rows.length === 0) return null;
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
    </div>
  );
}
