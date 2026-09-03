import { describe, expect, it } from 'vitest';
import {
  buildRoomSnapshot,
  isSnapshotFresh,
  MAX_SNAPSHOT_BYTES,
  ownClaimedCharacterIds,
  parseRoomSnapshot,
  SNAPSHOT_TTL_MS,
  snapshotKey,
  type RoomSnapshot,
} from './roomSnapshot';
import type { SkitScript } from '../../../shared/types';

const NOW = 1_700_000_000_000;

const script: SkitScript = {
  title: 'テスト台本',
  characters: [
    { id: 'c-heiter', name: 'ハイター', color: '#ffb86c' },
    { id: 'c-himmel', name: 'ヒンメル', color: '#7ecbff' },
  ],
  lines: [
    { id: 'l1', character: 'c-heiter', start: 0, end: 2, tokens: [{ t: 'こんにちは' }] },
  ],
};

const state = {
  claims: { 'c-heiter': 'u1', 'c-himmel': 'u2' },
  passScore: 85,
  rehearsalEnabled: false,
  users: [
    { id: 'u1', name: 'Oscar', color: '#fff', inVoice: false, muted: false },
    { id: 'u2', name: 'Yuki', color: '#fff', inVoice: false, muted: false },
  ],
};

function snap(overrides: Partial<RoomSnapshot> = {}): RoomSnapshot {
  return {
    script,
    claims: { ハイター: 'Oscar', ヒンメル: 'Yuki' },
    passScore: 85,
    rehearsalEnabled: false,
    savedAt: NOW,
    ...overrides,
  };
}

describe('snapshotKey', () => {
  it('is per-room and namespaced', () => {
    expect(snapshotKey('abc123')).toBe('serifu:roomSnapshot:abc123');
  });
});

describe('buildRoomSnapshot', () => {
  it('maps id-based claims to name-based claims', () => {
    const s = buildRoomSnapshot(script, state, NOW);
    expect(s.claims).toEqual({ ハイター: 'Oscar', ヒンメル: 'Yuki' });
    expect(s.passScore).toBe(85);
    expect(s.rehearsalEnabled).toBe(false);
    expect(s.savedAt).toBe(NOW);
    expect(s.script).toBe(script);
  });

  it('drops claims whose character or user is unresolvable', () => {
    const s = buildRoomSnapshot(
      script,
      { ...state, claims: { 'c-heiter': 'u-gone', 'c-unknown': 'u1', 'c-himmel': 'u2' } },
      NOW
    );
    expect(s.claims).toEqual({ ヒンメル: 'Yuki' });
  });
});

describe('parseRoomSnapshot', () => {
  it('round-trips a valid snapshot', () => {
    const parsed = parseRoomSnapshot(JSON.stringify(snap()));
    expect(parsed).not.toBeNull();
    expect(parsed?.script.title).toBe('テスト台本');
    expect(parsed?.claims['ハイター']).toBe('Oscar');
    expect(parsed?.passScore).toBe(85);
    expect(parsed?.rehearsalEnabled).toBe(false);
    expect(parsed?.savedAt).toBe(NOW);
  });

  it('rejects null, corrupt JSON, and non-objects', () => {
    expect(parseRoomSnapshot(null)).toBeNull();
    expect(parseRoomSnapshot('')).toBeNull();
    expect(parseRoomSnapshot('{oops')).toBeNull();
    expect(parseRoomSnapshot('"just a string"')).toBeNull();
    expect(parseRoomSnapshot('[1,2,3]')).toBeNull();
  });

  it('rejects snapshots with missing or mistyped fields', () => {
    const cases: Record<string, unknown>[] = [
      { ...snap(), script: undefined },
      { ...snap(), script: { title: 42, characters: [], lines: [] } },
      { ...snap(), script: { title: 'x', characters: 'nope', lines: [] } },
      { ...snap(), claims: ['not', 'a', 'record'] },
      { ...snap(), claims: { ハイター: 7 } },
      { ...snap(), passScore: 'high' as unknown as number },
      { ...snap(), passScore: Number.NaN },
      { ...snap(), rehearsalEnabled: 'yes' as unknown as boolean },
      { ...snap(), savedAt: undefined },
    ];
    for (const c of cases) {
      expect(parseRoomSnapshot(JSON.stringify(c))).toBeNull();
    }
  });
});

describe('isSnapshotFresh', () => {
  it('accepts snapshots younger than 24h', () => {
    expect(isSnapshotFresh(snap(), NOW + SNAPSHOT_TTL_MS - 1)).toBe(true);
    expect(isSnapshotFresh(snap(), NOW)).toBe(true);
  });

  it('rejects snapshots 24h or older, and future-stamped ones', () => {
    expect(isSnapshotFresh(snap(), NOW + SNAPSHOT_TTL_MS)).toBe(false);
    expect(isSnapshotFresh(snap({ savedAt: NOW + 1000 }), NOW)).toBe(false);
  });
});

describe('ownClaimedCharacterIds', () => {
  it('returns only the ids of roles the named user had claimed', () => {
    expect(ownClaimedCharacterIds(snap(), 'Oscar')).toEqual(['c-heiter']);
    expect(ownClaimedCharacterIds(snap(), 'Yuki')).toEqual(['c-himmel']);
  });

  it('returns nothing for users with no prior claim', () => {
    expect(ownClaimedCharacterIds(snap(), 'Newcomer')).toEqual([]);
  });

  it('ignores snapshot claims naming characters not in the script', () => {
    expect(
      ownClaimedCharacterIds(snap({ claims: { フリーレン: 'Oscar' } }), 'Oscar')
    ).toEqual([]);
  });
});

describe('MAX_SNAPSHOT_BYTES', () => {
  it('leaves headroom above the script size cap', () => {
    expect(MAX_SNAPSHOT_BYTES).toBeGreaterThan(1_500_000);
  });
});
