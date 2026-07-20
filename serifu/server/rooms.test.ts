import { describe, expect, it } from 'vitest';
import { RoomStore, validateScript } from './rooms';
import type { SkitScript } from '../shared/types';

function makeScript(): SkitScript {
  return {
    title: 'test scene',
    characters: [
      { id: 'a', name: 'Aoi', color: '#123456' },
      { id: 'b', name: 'Ben', color: '#654321' },
    ],
    lines: [
      { id: 'l1', character: 'a', start: 10, end: 12, tokens: [{ t: 'やあ' }] },
      { id: 'l2', character: 'b', start: 13, end: 15, tokens: [{ t: 'どうも' }] },
      { id: 'l3', character: null, start: 16, end: 18, tokens: [{ t: '（ナレーション）' }] },
    ],
  };
}

function setup(now: { t: number }) {
  const store = new RoomStore(() => now.t);
  store.join('room1', 'u1', 'Oscar');
  store.join('room1', 'u2', 'Yuki');
  store.loadScript('room1', makeScript());
  return store;
}

describe('validateScript', () => {
  it('accepts a well-formed script', () => {
    expect(validateScript(makeScript())).toBeNull();
  });
  it('rejects duplicate line ids', () => {
    const s = makeScript();
    s.lines[1]!.id = 'l1';
    expect(validateScript(s)).toMatch(/duplicate line id/);
  });
  it('rejects inverted times', () => {
    const s = makeScript();
    s.lines[0]!.start = 20;
    expect(validateScript(s)).toMatch(/start.*end/);
  });
  it('rejects non-object input', () => {
    expect(validateScript('nope')).not.toBeNull();
  });

  it('accepts scene chapters and rejects malformed ones', () => {
    const s = makeScript();
    s.scenes = [{ id: 's1', title: '約束', start: 0, end: 20 }];
    expect(validateScript(s)).toBeNull();
    const bad = makeScript();
    (bad as unknown as Record<string, unknown>).scenes = [{ id: 's1', title: '', start: 0, end: 20 }];
    expect(validateScript(bad)).toMatch(/scene/);
    const inverted = makeScript();
    inverted.scenes = [{ id: 's1', title: 'x', start: 30, end: 20 }];
    expect(validateScript(inverted)).toMatch(/scene/);
  });

  it('accepts vocab and grammar annotations', () => {
    const s = makeScript();
    s.lines[0]!.vocab = [{ w: '約束', r: 'やくそく', en: 'promise' }];
    s.lines[0]!.grammar = [{ p: '〜なら', en: 'conditional "if it\'s ~"' }];
    expect(validateScript(s)).toBeNull();
  });

  it('rejects malformed vocab and grammar', () => {
    const s = makeScript();
    (s.lines[0] as unknown as Record<string, unknown>).vocab = [{ w: '', en: 'x' }];
    expect(validateScript(s)).toMatch(/vocab/);
    const s2 = makeScript();
    (s2.lines[0] as unknown as Record<string, unknown>).grammar = [{ p: 'x' }];
    expect(validateScript(s2)).toMatch(/grammar/);
  });
});

describe('RoomStore basics', () => {
  it('joins, lists users, and cleans claims on leave', () => {
    const now = { t: 1000 };
    const store = setup(now);
    expect(store.claim('room1', 'a', 'u1')).toBe(true);
    let state = store.toState('room1');
    expect(state?.users).toHaveLength(2);
    expect(state?.claims.a).toBe('u1');

    store.leave('room1', 'u1');
    state = store.toState('room1');
    expect(state?.users).toHaveLength(1);
    expect(state?.claims.a).toBeUndefined();
  });

  it('prevents claiming an already-claimed character', () => {
    const now = { t: 1000 };
    const store = setup(now);
    expect(store.claim('room1', 'a', 'u1')).toBe(true);
    expect(store.claim('room1', 'a', 'u2')).toBe(false);
    expect(store.release('room1', 'a', 'u2')).toBe(false);
    expect(store.release('room1', 'a', 'u1')).toBe(true);
    expect(store.claim('room1', 'a', 'u2')).toBe(true);
  });

  it('extrapolates position while playing', () => {
    const now = { t: 1000 };
    const store = setup(now);
    store.play('room1', 100);
    now.t = 6000;
    const room = store.get('room1')!;
    expect(store.currentPosition(room)).toBeCloseTo(105);
    store.pause('room1', 105);
    now.t = 20000;
    expect(store.currentPosition(room)).toBeCloseTo(105);
  });
});

describe('rehearsal flow', () => {
  it('pauses at a claimed line and dedupes further requests', () => {
    const now = { t: 1000 };
    const store = setup(now);
    store.claim('room1', 'a', 'u1');
    store.play('room1', 9.5);
    now.t = 1600; // position ~10.1

    expect(store.rehearsalPause('room1', 'l1')).toBe(true);
    const state = store.toState('room1')!;
    expect(state.playback.isPlaying).toBe(false);
    expect(state.playback.position).toBe(10);
    expect(state.playback.pausedForLineId).toBe('l1');

    // Duplicate reports from other clients are no-ops (already paused).
    expect(store.rehearsalPause('room1', 'l1')).toBe(false);
  });

  it('ignores lines that are unclaimed or narration', () => {
    const now = { t: 1000 };
    const store = setup(now);
    store.play('room1', 12.5);
    now.t = 1600;
    expect(store.rehearsalPause('room1', 'l2')).toBe(false); // b unclaimed
    expect(store.rehearsalPause('room1', 'l3')).toBe(false); // narration
  });

  it('does not re-pause the same line right after resume', () => {
    const now = { t: 1000 };
    const store = setup(now);
    store.claim('room1', 'a', 'u1');
    store.play('room1', 9.9);
    now.t = 1200;
    expect(store.rehearsalPause('room1', 'l1')).toBe(true);
    expect(store.rehearsalResume('room1')).toBe(true);
    expect(store.toState('room1')?.playback.isPlaying).toBe(true);

    // A lagging client reports the same crossing again — must be ignored.
    now.t = 2000;
    expect(store.rehearsalPause('room1', 'l1')).toBe(false);

    // But replaying after a backward seek re-arms the pause.
    now.t = 3000;
    store.seek('room1', 9.5);
    now.t = 3600;
    expect(store.rehearsalPause('room1', 'l1')).toBe(true);
  });

  it('rejects pause reports far from the line start', () => {
    const now = { t: 1000 };
    const store = setup(now);
    store.claim('room1', 'a', 'u1');
    store.play('room1', 100);
    now.t = 1200;
    expect(store.rehearsalPause('room1', 'l1')).toBe(false);
  });

  it('clears the paused marker on manual play/seek', () => {
    const now = { t: 1000 };
    const store = setup(now);
    store.claim('room1', 'a', 'u1');
    store.play('room1', 9.9);
    now.t = 1200;
    store.rehearsalPause('room1', 'l1');
    store.seek('room1', 50);
    expect(store.toState('room1')?.playback.pausedForLineId).toBeNull();
  });
});

describe('script loading', () => {
  it('drops claims for characters that no longer exist', () => {
    const now = { t: 1000 };
    const store = setup(now);
    store.claim('room1', 'a', 'u1');
    store.claim('room1', 'b', 'u2');
    const next = makeScript();
    next.characters = [next.characters[0]!];
    expect(store.loadScript('room1', next)).toBeNull();
    const state = store.toState('room1')!;
    expect(state.claims.a).toBe('u1');
    expect(state.claims.b).toBeUndefined();
    expect(state.scriptVersion).toBe(2);
  });

  it('sorts lines by start time', () => {
    const now = { t: 1000 };
    const store = setup(now);
    const scrambled = makeScript();
    scrambled.lines.reverse();
    store.loadScript('room1', scrambled);
    const room = store.get('room1')!;
    expect(room.script?.lines.map((l) => l.id)).toEqual(['l1', 'l2', 'l3']);
  });
});

describe('pass threshold + practice stats', () => {
  it('clamps the threshold into the sane range', () => {
    const now = { t: 1000 };
    const store = setup(now);
    store.setPassScore('room1', 85);
    expect(store.toState('room1')?.passScore).toBe(85);
    store.setPassScore('room1', 5);
    expect(store.toState('room1')?.passScore).toBe(40);
    store.setPassScore('room1', 200);
    expect(store.toState('room1')?.passScore).toBe(95);
    expect(store.setPassScore('room1', Number.NaN)).toBe(false);
  });

  it('tallies attempts against the room threshold', () => {
    const now = { t: 1000 };
    const store = setup(now);
    expect(store.recordAttempt('room1', 'u1', 40)).toBe(false);
    expect(store.recordAttempt('room1', 'u1', 90)).toBe(true);
    const stats = store.toState('room1')?.stats.u1;
    expect(stats).toEqual({ attempts: 2, passes: 1, scoreSum: 130 });
    // Unknown users are rejected.
    expect(store.recordAttempt('room1', 'ghost', 90)).toBeNull();
  });

  it('threshold changes affect subsequent attempts', () => {
    const now = { t: 1000 };
    const store = setup(now);
    store.setPassScore('room1', 85);
    expect(store.recordAttempt('room1', 'u1', 80)).toBe(false);
    store.setPassScore('room1', 55);
    expect(store.recordAttempt('room1', 'u1', 80)).toBe(true);
  });

  it('resets stats when a new script loads, and drops them on leave', () => {
    const now = { t: 1000 };
    const store = setup(now);
    store.recordAttempt('room1', 'u1', 90);
    store.recordAttempt('room1', 'u2', 90);
    store.loadScript('room1', makeScript());
    expect(store.toState('room1')?.stats).toEqual({});
    store.recordAttempt('room1', 'u2', 90);
    store.leave('room1', 'u2');
    expect(store.toState('room1')?.stats.u2).toBeUndefined();
  });
});

describe('gc', () => {
  it('removes rooms only after they have been empty long enough', () => {
    const now = { t: 1000 };
    const store = new RoomStore(() => now.t);
    store.join('r1', 'u1', 'A');
    store.leave('r1', 'u1');
    now.t = 1000 + 10 * 60_000;
    expect(store.gc(30 * 60_000)).toBe(0);
    now.t = 1000 + 31 * 60_000;
    expect(store.gc(30 * 60_000)).toBe(1);
    expect(store.get('r1')).toBeUndefined();
  });
});
