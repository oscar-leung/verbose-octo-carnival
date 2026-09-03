import { describe, expect, it } from 'vitest';
import {
  avgScore,
  buildRecapData,
  buildRecapRows,
  formatRecapDate,
  MAX_RECAP_ROWS,
  truncateForCard,
} from './recapCard';
import type { RoomUser, UserStats } from '../../../shared/types';

function user(id: string, name: string, color = '#7ecbff'): RoomUser {
  return { id, name, color, inVoice: false, muted: false };
}

describe('avgScore', () => {
  it('rounds the running average', () => {
    expect(avgScore({ attempts: 3, passes: 2, scoreSum: 250 })).toBe(83);
  });

  it('is 0 with no attempts (no divide-by-zero)', () => {
    expect(avgScore({ attempts: 0, passes: 0, scoreSum: 0 })).toBe(0);
  });
});

describe('buildRecapRows', () => {
  const users = [user('a', 'Oscar'), user('b', 'Yuki', '#ffb86c'), user('c', 'Mika')];
  const stats: Record<string, UserStats> = {
    a: { attempts: 2, passes: 1, scoreSum: 150 },
    b: { attempts: 4, passes: 4, scoreSum: 380 },
    c: { attempts: 0, passes: 0, scoreSum: 0 },
  };

  it('keeps only users with attempts, sorted by average score', () => {
    const rows = buildRecapRows(users, stats, 'a');
    expect(rows.map((r) => r.name)).toEqual(['Yuki', 'Oscar']);
    expect(rows[0]).toMatchObject({ passes: 4, attempts: 4, avg: 95, isSelf: false });
    expect(rows[1]).toMatchObject({ passes: 1, attempts: 2, avg: 75, isSelf: true });
  });

  it('carries the user color through', () => {
    expect(buildRecapRows(users, stats, 'a')[0]?.color).toBe('#ffb86c');
  });

  it('breaks average ties by pass count', () => {
    const tied: Record<string, UserStats> = {
      a: { attempts: 2, passes: 2, scoreSum: 160 },
      b: { attempts: 2, passes: 1, scoreSum: 160 },
    };
    expect(buildRecapRows(users, tied, 'b').map((r) => r.name)).toEqual(['Oscar', 'Yuki']);
  });

  it('caps the card at MAX_RECAP_ROWS rows', () => {
    const many = Array.from({ length: 12 }, (_, i) => user(`u${i}`, `P${i}`));
    const s = Object.fromEntries(
      many.map((u) => [u.id, { attempts: 1, passes: 1, scoreSum: 90 }])
    );
    expect(buildRecapRows(many, s, 'u0')).toHaveLength(MAX_RECAP_ROWS);
  });

  it('handles missing stats entries', () => {
    expect(buildRecapRows([user('x', 'Ghost')], {}, 'x')).toEqual([]);
  });
});

describe('truncateForCard', () => {
  it('leaves short text alone', () => {
    expect(truncateForCard('ハイター', 12)).toBe('ハイター');
  });

  it('clips long text with one ellipsis inside the budget', () => {
    const out = truncateForCard('葬送の長い長い長いタイトルのテスト台本', 10);
    expect(out).toBe('葬送の長い長い長い…');
    expect([...out]).toHaveLength(10);
  });

  it('counts astral characters as one (no surrogate splits)', () => {
    expect(truncateForCard('𠮷野家テスト', 3)).toBe('𠮷野…');
  });
});

describe('formatRecapDate', () => {
  it('zero-pads to YYYY.MM.DD', () => {
    expect(formatRecapDate(new Date(2026, 8, 3))).toBe('2026.09.03');
  });
});

describe('buildRecapData', () => {
  it('falls back to a neutral title when none is loaded', () => {
    const d = buildRecapData(null, [], {}, 'a', new Date(2026, 0, 1));
    expect(d.scriptTitle).toBe('Serifu セッション');
    expect(d.dateLabel).toBe('2026.01.01');
    expect(d.rows).toEqual([]);
  });

  it('truncates a very long script title', () => {
    const long = 'と'.repeat(40);
    const d = buildRecapData(long, [], {}, 'a');
    expect([...d.scriptTitle]).toHaveLength(26);
    expect(d.scriptTitle.endsWith('…')).toBe(true);
  });
});
