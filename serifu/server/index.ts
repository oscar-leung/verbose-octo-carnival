import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import express from 'express';
import { Server, type Socket } from 'socket.io';
import { RoomStore } from './rooms';
import { createBucket, tryTake } from './rateLimit';
import {
  MAX_SCRIPT_JSON_BYTES,
  ROOM_ID_PATTERN,
  type ClientToServerEvents,
  type ServerToClientEvents,
} from '../shared/types';

interface SocketData {
  roomId?: string;
}

type AppSocket = Socket<ClientToServerEvents, ServerToClientEvents, Record<string, never>, SocketData>;

const dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT ?? 3001);
const distDir = path.resolve(dirname, '../dist');

const app = express();
const server = http.createServer(app);
const io = new Server<ClientToServerEvents, ServerToClientEvents, Record<string, never>, SocketData>(
  server,
  {
    // Scripts are sent as one JSON payload; allow a bit above the script cap.
    maxHttpBufferSize: 2_000_000,
  }
);

const store = new RoomStore();

// Per-socket event rate limit. Generous on purpose: normal usage (playback
// sync, rehearsal, rapid speech retries) stays far below it; only a runaway
// or abusive client ever hits it. Exceeding events are dropped silently.
const RATE_LIMIT_EVENTS = 40;
const RATE_LIMIT_WINDOW_MS = 10_000;

app.get('/healthz', (_req, res) => {
  res.json({ ok: true });
});
// ICE servers for voice chat. STUN alone covers most home networks; for
// strict NATs set TURN_URLS (comma-separated), TURN_USERNAME, and
// TURN_CREDENTIAL in the environment (e.g. a free metered.ca account) and
// clients pick them up with no code change.
app.get('/api/ice', (_req, res) => {
  const iceServers: { urls: string; username?: string; credential?: string }[] = [
    { urls: 'stun:stun.l.google.com:19302' },
  ];
  const turnUrls = (process.env.TURN_URLS ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  const username = process.env.TURN_USERNAME;
  const credential = process.env.TURN_CREDENTIAL;
  for (const urls of turnUrls) {
    iceServers.push({
      urls,
      ...(username ? { username } : {}),
      ...(credential ? { credential } : {}),
    });
  }
  res.json({ iceServers });
});
// dotfiles: 'allow' so /.well-known/assetlinks.json (Play Store TWA domain
// verification) is served rather than ignored.
app.use(express.static(distDir, { dotfiles: 'allow' }));
// SPA fallback: any other GET serves the client shell (no-op in dev, where
// the Vite dev server owns the pages and proxies /socket.io here).
app.use((req, res, next) => {
  if (req.method !== 'GET') {
    next();
    return;
  }
  res.sendFile(path.join(distDir, 'index.html'), (err) => {
    if (err) next();
  });
});

function syncRoom(roomId: string): void {
  const state = store.toState(roomId);
  if (state) io.to(roomId).emit('room:state', state);
}

function leaveCurrentRoom(socket: AppSocket): void {
  const roomId = socket.data.roomId;
  if (!roomId) return;
  socket.data.roomId = undefined;
  void socket.leave(roomId);
  if (store.leave(roomId, socket.id)) syncRoom(roomId);
}

io.on('connection', (socket: AppSocket) => {
  const bucket = createBucket(RATE_LIMIT_EVENTS, RATE_LIMIT_WINDOW_MS, Date.now());
  let droppedEvents = 0;
  socket.use((event, next) => {
    if (tryTake(bucket, Date.now())) {
      next();
      return;
    }
    // Drop silently: no error to the client, no disconnect. Log once.
    droppedEvents += 1;
    if (droppedEvents === 1) {
      console.warn(
        `[serifu] rate limit exceeded by socket ${socket.id}; dropping events (first: ${String(event[0])})`
      );
    }
  });
  socket.on('disconnect', () => {
    if (droppedEvents > 0) {
      console.warn(`[serifu] socket ${socket.id} disconnected; ${droppedEvents} events were rate-limited`);
    }
  });

  socket.on('room:join', (p, ack) => {
    if (typeof ack !== 'function') return;
    if (typeof p?.roomId !== 'string' || !ROOM_ID_PATTERN.test(p.roomId)) {
      ack({ ok: false, error: 'Invalid room id.' });
      return;
    }
    if (typeof p.name !== 'string') {
      ack({ ok: false, error: 'Invalid name.' });
      return;
    }
    leaveCurrentRoom(socket);
    const roomId = p.roomId.toLowerCase();
    const joined = store.join(roomId, socket.id, p.name);
    if ('error' in joined) {
      ack({ ok: false, error: joined.error });
      return;
    }
    socket.data.roomId = roomId;
    void socket.join(roomId);
    const state = store.toState(roomId);
    if (!state) {
      ack({ ok: false, error: 'Room vanished, try again.' });
      return;
    }
    ack({ ok: true, selfId: socket.id, state, script: store.get(roomId)?.script ?? null });
    syncRoom(roomId);
  });

  socket.on('playback:play', (p) => {
    const roomId = socket.data.roomId;
    if (!roomId || typeof p?.position !== 'number') return;
    if (store.play(roomId, p.position)) syncRoom(roomId);
  });

  socket.on('playback:pause', (p) => {
    const roomId = socket.data.roomId;
    if (!roomId || typeof p?.position !== 'number') return;
    if (store.pause(roomId, p.position)) syncRoom(roomId);
  });

  socket.on('playback:seek', (p) => {
    const roomId = socket.data.roomId;
    if (!roomId || typeof p?.position !== 'number') return;
    if (store.seek(roomId, p.position)) syncRoom(roomId);
  });

  socket.on('rehearsal:set', (p) => {
    const roomId = socket.data.roomId;
    if (!roomId || typeof p?.enabled !== 'boolean') return;
    if (store.setRehearsal(roomId, p.enabled)) syncRoom(roomId);
  });

  socket.on('rehearsal:threshold', (p) => {
    const roomId = socket.data.roomId;
    if (!roomId || typeof p?.score !== 'number') return;
    if (store.setPassScore(roomId, p.score)) syncRoom(roomId);
  });

  socket.on('rehearsal:pause', (p) => {
    const roomId = socket.data.roomId;
    if (!roomId || typeof p?.lineId !== 'string') return;
    if (store.rehearsalPause(roomId, p.lineId)) syncRoom(roomId);
  });

  socket.on('rehearsal:resume', () => {
    const roomId = socket.data.roomId;
    if (!roomId) return;
    if (store.rehearsalResume(roomId)) syncRoom(roomId);
  });

  socket.on('character:claim', (p) => {
    const roomId = socket.data.roomId;
    if (!roomId || typeof p?.characterId !== 'string') return;
    if (store.claim(roomId, p.characterId, socket.id)) syncRoom(roomId);
  });

  socket.on('character:release', (p) => {
    const roomId = socket.data.roomId;
    if (!roomId || typeof p?.characterId !== 'string') return;
    if (store.release(roomId, p.characterId, socket.id)) syncRoom(roomId);
  });

  socket.on('script:load', (p, ack) => {
    if (typeof ack !== 'function') return;
    const roomId = socket.data.roomId;
    if (!roomId) {
      ack({ ok: false, error: 'Join a room first.' });
      return;
    }
    let size: number;
    try {
      size = JSON.stringify(p?.script).length;
    } catch {
      ack({ ok: false, error: 'Script is not valid JSON data.' });
      return;
    }
    if (size > MAX_SCRIPT_JSON_BYTES) {
      ack({ ok: false, error: 'Script is too large.' });
      return;
    }
    const error = store.loadScript(roomId, p.script);
    if (error) {
      ack({ ok: false, error });
      return;
    }
    ack({ ok: true });
    io.to(roomId).emit('script:state', store.get(roomId)?.script ?? null);
    syncRoom(roomId);
  });

  socket.on('voice:state', (p) => {
    const roomId = socket.data.roomId;
    if (!roomId || typeof p?.inVoice !== 'boolean' || typeof p?.muted !== 'boolean') return;
    if (store.setVoice(roomId, socket.id, p.inVoice, p.muted)) syncRoom(roomId);
  });

  socket.on('speech:attempt', (p) => {
    const roomId = socket.data.roomId;
    if (
      !roomId ||
      typeof p?.lineId !== 'string' ||
      p.lineId.length > 64 ||
      typeof p?.transcript !== 'string' ||
      typeof p?.score !== 'number' ||
      typeof p?.passed !== 'boolean'
    ) {
      return;
    }
    const user = store.get(roomId)?.users.get(socket.id);
    if (!user) return;
    // The room threshold is authoritative for pass/fail and the tally.
    const passed = store.recordAttempt(roomId, socket.id, p.score);
    if (passed === null) return;
    io.to(roomId).emit('speech:attempt', {
      lineId: p.lineId,
      transcript: p.transcript.slice(0, 300),
      score: Math.max(0, Math.min(100, Math.round(p.score))),
      passed,
      userId: socket.id,
      userName: user.name,
    });
    syncRoom(roomId);
  });

  socket.on('webrtc:signal', (p) => {
    const roomId = socket.data.roomId;
    if (!roomId || typeof p?.to !== 'string' || typeof p?.data !== 'object' || p.data === null) {
      return;
    }
    // Only relay between members of the same room.
    if (!store.get(roomId)?.users.has(p.to)) return;
    io.to(p.to).emit('webrtc:signal', { from: socket.id, data: p.data });
  });

  socket.on('disconnect', () => {
    leaveCurrentRoom(socket);
  });
});

const gcTimer = setInterval(() => store.gc(30 * 60_000), 10 * 60_000);
gcTimer.unref();

// Hourly sweep: reap rooms with no accepted events for >24h even if
// half-dead sockets are still nominally joined; kick those sockets out so
// their next join starts clean.
const IDLE_ROOM_MAX_MS = 24 * 60 * 60_000;
const sweepTimer = setInterval(() => {
  const removed = store.sweepIdle(IDLE_ROOM_MAX_MS);
  for (const roomId of removed) {
    // Detach lingering sockets so their stale roomId can't touch a future
    // room recreated under the same id.
    void io
      .in(roomId)
      .fetchSockets()
      .then((sockets) => {
        for (const s of sockets) {
          s.data.roomId = undefined;
          s.leave(roomId);
        }
      })
      .catch(() => {});
  }
  if (removed.length > 0) {
    console.log(`[serifu] swept ${removed.length} idle room(s): ${removed.join(', ')}`);
  }
}, 60 * 60_000);
sweepTimer.unref();

server.listen(PORT, () => {
  console.log(`[serifu] listening on http://localhost:${PORT}`);
});
