import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import express from 'express';
import { Server, type Socket } from 'socket.io';
import { RoomStore } from './rooms';
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

app.get('/healthz', (_req, res) => {
  res.json({ ok: true });
});
app.use(express.static(distDir));
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
    io.to(roomId).emit('speech:attempt', {
      lineId: p.lineId,
      transcript: p.transcript.slice(0, 300),
      score: Math.max(0, Math.min(100, Math.round(p.score))),
      passed: p.passed,
      userId: socket.id,
      userName: user.name,
    });
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

server.listen(PORT, () => {
  console.log(`[serifu] listening on http://localhost:${PORT}`);
});
