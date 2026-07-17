import { useEffect, useRef, useState, type ChangeEvent, type MutableRefObject } from 'react';
import type { PlaybackState, SkitScript } from '../../../shared/types';
import type { RoomActions } from '../lib/useRoom';
import { expectedPosition, formatTime } from '../lib/playback';

interface Props {
  playback: PlaybackState;
  script: SkitScript | null;
  claims: Record<string, string>;
  rehearsalEnabled: boolean;
  actions: RoomActions;
  serverNow: () => number;
  /** Local lead/lag vs. the room, to compensate for different encodes. */
  userOffset: number;
  /** Written by this panel so the rest of the UI can read the video clock. */
  videoPosRef: MutableRefObject<number | null>;
}

export default function VideoPanel({
  playback,
  script,
  claims,
  rehearsalEnabled,
  actions,
  serverNow,
  userOffset,
  videoPosRef,
}: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const prevPosRef = useRef<number | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [ready, setReady] = useState(0);
  const [needsGesture, setNeedsGesture] = useState(false);
  const [displayTime, setDisplayTime] = useState(0);
  const [volume, setVolume] = useState(1);

  const scriptEnd = script?.lines.length
    ? Math.max(...script.lines.map((l) => l.end)) + 30
    : 1500;

  /** Current position in room-time (shared timeline). */
  const roomPos = (): number => {
    const v = videoRef.current;
    if (v && videoUrl) return v.currentTime - userOffset;
    return expectedPosition(playback, serverNow());
  };

  const togglePlay = () => {
    if (playback.pausedForLineId) {
      actions.rehearsalResume();
    } else if (playback.isPlaying) {
      actions.pause(roomPos());
    } else {
      actions.play(roomPos());
    }
  };

  const onFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setVideoUrl(URL.createObjectURL(file));
    setFileName(file.name);
    setDuration(null);
    prevPosRef.current = null;
  };

  // Revoke the previous object URL when it is replaced or on unmount.
  useEffect(() => {
    if (!videoUrl) return;
    return () => URL.revokeObjectURL(videoUrl);
  }, [videoUrl]);

  // Clear the shared video clock when there is no local video.
  useEffect(() => {
    if (!videoUrl) videoPosRef.current = null;
  }, [videoUrl, videoPosRef]);

  // Reconcile the local <video> with the room's playback state, then keep
  // correcting drift every couple of seconds while playing.
  useEffect(() => {
    const reconcile = () => {
      const v = videoRef.current;
      if (!v || !videoUrl) return;
      const target = expectedPosition(playback, serverNow()) + userOffset;
      const drift = Math.abs(v.currentTime - target);
      if (drift > (playback.isPlaying ? 0.75 : 0.35)) {
        v.currentTime = Math.max(0, target);
      }
      if (playback.isPlaying && v.paused) {
        v.play()
          .then(() => setNeedsGesture(false))
          .catch(() => setNeedsGesture(true));
      } else if (!playback.isPlaying && !v.paused) {
        v.pause();
      }
    };
    reconcile();
    const timer = setInterval(() => {
      if (playback.isPlaying) reconcile();
    }, 2000);
    return () => clearInterval(timer);
  }, [playback, userOffset, videoUrl, ready, serverNow]);

  // Fast loop: publish the video clock, update the time display, and detect
  // crossings into claimed lines for rehearsal auto-pause.
  useEffect(() => {
    if (!videoUrl) return;
    const timer = setInterval(() => {
      const v = videoRef.current;
      if (!v) return;
      const cur = v.currentTime - userOffset;
      const prev = prevPosRef.current;
      prevPosRef.current = cur;
      videoPosRef.current = cur;
      setDisplayTime(Math.round(v.currentTime * 10) / 10);
      if (!script || !rehearsalEnabled || !playback.isPlaying || v.paused) return;
      // Ignore first sample, backwards motion, and big jumps (seeks).
      if (prev === null || cur <= prev || cur - prev > 1.5) return;
      for (const line of script.lines) {
        if (line.start > cur) break;
        if (
          line.character !== null &&
          prev < line.start &&
          cur >= line.start &&
          claims[line.character] !== undefined
        ) {
          actions.rehearsalPause(line.id);
          break;
        }
      }
    }, 120);
    return () => clearInterval(timer);
  }, [videoUrl, script, claims, rehearsalEnabled, playback.isPlaying, userOffset, actions, videoPosRef]);

  useEffect(() => {
    const v = videoRef.current;
    if (v) v.volume = volume;
  }, [volume, videoUrl]);

  const sliderMax = videoUrl ? (duration ?? scriptEnd) : scriptEnd;
  const sliderValue = videoUrl
    ? Math.min(displayTime, sliderMax)
    : Math.min(Math.max(expectedPosition(playback, serverNow()), 0), sliderMax);

  return (
    <div className="video-panel">
      {videoUrl ? (
        <video
          ref={videoRef}
          src={videoUrl}
          playsInline
          onClick={togglePlay}
          onLoadedMetadata={(e) => {
            setDuration(e.currentTarget.duration);
            setReady((n) => n + 1);
          }}
        />
      ) : (
        <div className="video-placeholder">
          <p>みんなそれぞれ、自分の動画ファイルを開いてね</p>
          <p className="muted">
            Everyone opens their own copy of the episode — nothing is uploaded, playback just
            stays in sync. No file? You can still follow the script and voice chat.
          </p>
          <label className="file-button primary">
            📁 動画を選ぶ / choose episode file
            <input type="file" accept="video/*,.mkv" onChange={onFile} hidden />
          </label>
        </div>
      )}
      {needsGesture && videoUrl && (
        <button
          className="gesture-overlay"
          onClick={() => {
            setNeedsGesture(false);
            videoRef.current?.play().catch(() => setNeedsGesture(true));
          }}
        >
          ▶ タップで同期 / click to sync
        </button>
      )}
      <div className="controls">
        <button className="play-btn" onClick={togglePlay}>
          {playback.isPlaying ? '⏸' : '▶'}
        </button>
        <button onClick={() => actions.seek(Math.max(0, roomPos() - 5))} title="back 5s (←)">
          ↺5
        </button>
        <button onClick={() => actions.seek(roomPos() + 5)} title="forward 5s (→)">
          5↻
        </button>
        <span className="time">
          {formatTime(videoUrl ? displayTime : sliderValue)}
          {duration !== null ? ` / ${formatTime(duration)}` : ''}
        </span>
        <input
          className="seek"
          type="range"
          min={0}
          max={sliderMax}
          step={0.1}
          value={sliderValue}
          onChange={(e) => {
            const t = Number(e.target.value);
            actions.seek(Math.max(0, videoUrl ? t - userOffset : t));
          }}
        />
        <input
          className="volume"
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={volume}
          onChange={(e) => setVolume(Number(e.target.value))}
          title="local volume"
        />
        {videoUrl && (
          <label className="file-button small" title={fileName ?? undefined}>
            📁
            <input type="file" accept="video/*,.mkv" onChange={onFile} hidden />
          </label>
        )}
      </div>
    </div>
  );
}
