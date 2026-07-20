import { useEffect, useRef, useState, type ChangeEvent } from 'react';

/**
 * Loop a local music file (e.g. your own copy of the OST) softly under the
 * session. Audio stays on this device — every listener brings their own copy,
 * exactly like the episode video.
 */
export default function BgmPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [name, setName] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [volume, setVolume] = useState(0.3);

  const onFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUrl(URL.createObjectURL(file));
    setName(file.name);
    setPlaying(false);
  };

  useEffect(() => {
    if (!url) return;
    return () => URL.revokeObjectURL(url);
  }, [url]);

  useEffect(() => {
    const a = audioRef.current;
    if (a) a.volume = volume;
  }, [volume, url]);

  const toggle = () => {
    const a = audioRef.current;
    if (!a) return;
    if (a.paused) {
      a.play()
        .then(() => setPlaying(true))
        .catch(() => setPlaying(false));
    } else {
      a.pause();
      setPlaying(false);
    }
  };

  return (
    <div className="bgm-panel">
      <span className="bar-label">BGM</span>
      <label className="file-button small" title="loop a local music file — plays only for you">
        🎵 {name ? name.slice(0, 24) : 'load a track (e.g. your OST copy)'}
        <input type="file" accept="audio/*" onChange={onFile} hidden />
      </label>
      {url && (
        <>
          <audio ref={audioRef} src={url} loop />
          <button className="chip" onClick={toggle}>
            {playing ? '⏸ pause' : '▶ play'}
          </button>
          <input
            className="bgm-volume"
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
            title="BGM volume (only you hear this)"
          />
        </>
      )}
      <span className="muted bgm-note">plays only for you — keep it under the dialogue</span>
    </div>
  );
}
