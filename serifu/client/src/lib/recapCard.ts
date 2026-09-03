import type { RoomUser, UserStats } from '../../../shared/types';

/** Fixed export size — 4:5 portrait, the friendliest share aspect. */
export const RECAP_WIDTH = 1080;
export const RECAP_HEIGHT = 1350;

/** More rows than this won't fit the card; keep the busiest practicers. */
export const MAX_RECAP_ROWS = 8;

export interface RecapRow {
  name: string;
  color: string;
  passes: number;
  attempts: number;
  /** Rounded average score 0-100. */
  avg: number;
  isSelf: boolean;
}

export interface RecapData {
  scriptTitle: string;
  rows: RecapRow[];
  /** Pre-formatted date label, e.g. 2026.09.03 */
  dateLabel: string;
}

/** Rounded average score for a tally (0 when there are no attempts). */
export function avgScore(s: UserStats): number {
  return s.attempts > 0 ? Math.round(s.scoreSum / s.attempts) : 0;
}

/**
 * Per-user recap rows: everyone with ≥1 attempt, best average first
 * (ties: more passes first), capped so the card never overflows.
 */
export function buildRecapRows(
  users: RoomUser[],
  stats: Record<string, UserStats>,
  selfId: string
): RecapRow[] {
  return users
    .map((u) => ({ u, s: stats[u.id] }))
    .filter((r): r is { u: RoomUser; s: UserStats } => !!r.s && r.s.attempts > 0)
    .map(({ u, s }) => ({
      name: u.name,
      color: u.color,
      passes: s.passes,
      attempts: s.attempts,
      avg: avgScore(s),
      isSelf: u.id === selfId,
    }))
    .sort((a, b) => b.avg - a.avg || b.passes - a.passes)
    .slice(0, MAX_RECAP_ROWS);
}

/** Clip to `max` characters, replacing the overflow with a single ellipsis. */
export function truncateForCard(text: string, max: number): string {
  const chars = [...text];
  if (chars.length <= max) return text;
  return chars.slice(0, Math.max(0, max - 1)).join('') + '…';
}

/** 2026.09.03-style date label — reads the same in both languages. */
export function formatRecapDate(d: Date): string {
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}.${mm}.${dd}`;
}

/** Assemble everything the drawing pass needs from live room state. */
export function buildRecapData(
  scriptTitle: string | null | undefined,
  users: RoomUser[],
  stats: Record<string, UserStats>,
  selfId: string,
  now: Date = new Date()
): RecapData {
  return {
    scriptTitle: truncateForCard((scriptTitle ?? '').trim() || 'Serifu セッション', 26),
    rows: buildRecapRows(users, stats, selfId),
    dateLabel: formatRecapDate(now),
  };
}

const JP_FONT = '"Hiragino Sans", "Noto Sans JP", "Yu Gothic", sans-serif';

/** Deterministic star field so the same session renders the same sky. */
function drawStars(ctx: CanvasRenderingContext2D) {
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) % 2147483648;
    return seed / 2147483648;
  };
  for (let i = 0; i < 60; i++) {
    const x = rand() * RECAP_WIDTH;
    const y = rand() * RECAP_HEIGHT * 0.8;
    const r = 1 + rand() * 2.2;
    ctx.globalAlpha = 0.25 + rand() * 0.6;
    ctx.fillStyle = rand() > 0.8 ? '#7ecbff' : '#e8ecf4';
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

/**
 * Paint the 1080x1350 recap card. Pure canvas drawing — no DOM lookups,
 * no state; everything comes in through `data`.
 */
export function drawRecapCard(canvas: HTMLCanvasElement, data: RecapData): void {
  canvas.width = RECAP_WIDTH;
  canvas.height = RECAP_HEIGHT;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  // Night sky backdrop.
  const bg = ctx.createLinearGradient(0, 0, 0, RECAP_HEIGHT);
  bg.addColorStop(0, '#0b1226');
  bg.addColorStop(1, '#1d1a26');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, RECAP_WIDTH, RECAP_HEIGHT);
  drawStars(ctx);

  // Wordmark.
  ctx.textAlign = 'center';
  ctx.fillStyle = '#7ecbff';
  ctx.font = `600 64px ${JP_FONT}`;
  ctx.fillText('Serifu 台詞', RECAP_WIDTH / 2, 150);
  ctx.fillStyle = '#8b93a7';
  ctx.font = `400 34px ${JP_FONT}`;
  ctx.fillText('練習のきろく / practice recap', RECAP_WIDTH / 2, 210);

  // Script title — shrink to fit rather than clipping at the edges.
  ctx.fillStyle = '#e8ecf4';
  let titleSize = 58;
  ctx.font = `700 ${titleSize}px ${JP_FONT}`;
  while (titleSize > 30 && ctx.measureText(data.scriptTitle).width > RECAP_WIDTH - 140) {
    titleSize -= 2;
    ctx.font = `700 ${titleSize}px ${JP_FONT}`;
  }
  ctx.fillText(data.scriptTitle, RECAP_WIDTH / 2, 330);

  // Divider.
  ctx.strokeStyle = 'rgba(126, 203, 255, 0.35)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(140, 390);
  ctx.lineTo(RECAP_WIDTH - 140, 390);
  ctx.stroke();

  // Per-user rows.
  const rowH = 96;
  const top = 460;
  const left = 110;
  const right = RECAP_WIDTH - 110;
  data.rows.forEach((row, i) => {
    const y = top + i * rowH;
    if (row.isSelf) {
      ctx.fillStyle = 'rgba(126, 203, 255, 0.12)';
      ctx.strokeStyle = '#7ecbff';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.roundRect(left - 26, y - 56, right - left + 52, 80, 18);
      ctx.fill();
      ctx.stroke();
    }
    // Color dot for the user.
    ctx.fillStyle = row.color;
    ctx.beginPath();
    ctx.arc(left + 14, y - 14, 12, 0, Math.PI * 2);
    ctx.fill();
    // Name (self gets a star, like the live stats bar).
    ctx.textAlign = 'left';
    ctx.fillStyle = row.isSelf ? '#ffffff' : '#e8ecf4';
    ctx.font = `${row.isSelf ? 700 : 500} 42px ${JP_FONT}`;
    ctx.fillText(truncateForCard(row.name, 12) + (row.isSelf ? ' ★' : ''), left + 48, y);
    // Tally, right-aligned.
    ctx.textAlign = 'right';
    ctx.fillStyle = '#7ecbff';
    ctx.font = `600 42px ${JP_FONT}`;
    ctx.fillText(`${row.passes}/${row.attempts} · ${row.avg}%`, right, y);
  });

  // Date + footer.
  ctx.textAlign = 'center';
  ctx.fillStyle = '#8b93a7';
  ctx.font = `400 34px ${JP_FONT}`;
  ctx.fillText(data.dateLabel, RECAP_WIDTH / 2, RECAP_HEIGHT - 130);
  ctx.fillStyle = '#5b6478';
  ctx.font = `400 30px ${JP_FONT}`;
  ctx.fillText('serifu — speak your favorite scenes', RECAP_WIDTH / 2, RECAP_HEIGHT - 70);
}
