import { useState, type ChangeEvent } from 'react';
import type { Character, ScriptLine, SkitScript } from '../../../shared/types';
import type { RoomActions } from '../lib/useRoom';
import { parseCues, parseRubyText, rubyTokensToText } from '../lib/srt';
import { parseTimeInput } from '../lib/playback';
import { loadLibrary, removeFromLibrary, saveToLibrary, type LibraryEntry } from '../lib/scriptLibrary';
import { DEMO_SCENES } from '../data/demoScenes';

interface Props {
  script: SkitScript | null;
  actions: RoomActions;
  onClose: () => void;
}

interface DraftLine {
  key: number;
  character: string;
  startText: string;
  endText: string;
  text: string;
  translation: string;
}

const CHAR_COLORS = [
  '#7ecbff',
  '#b4befe',
  '#a6e3a1',
  '#ffb86c',
  '#f38ba8',
  '#f9e2af',
  '#94e2d5',
  '#cba6f7',
];

let keyCounter = 1;
const nextKey = () => keyCounter++;

function lineToDraft(line: ScriptLine): DraftLine {
  return {
    key: nextKey(),
    character: line.character ?? '',
    startText: line.start.toFixed(1),
    endText: line.end.toFixed(1),
    text: rubyTokensToText(line.tokens),
    translation: line.translation ?? '',
  };
}

function scriptToDraft(s: SkitScript): { title: string; chars: Character[]; lines: DraftLine[] } {
  return { title: s.title, chars: s.characters, lines: s.lines.map(lineToDraft) };
}

function looksLikeScript(value: unknown): value is SkitScript {
  return (
    typeof value === 'object' &&
    value !== null &&
    Array.isArray((value as SkitScript).lines) &&
    Array.isArray((value as SkitScript).characters)
  );
}

export default function ScriptEditor({ script, actions, onClose }: Props) {
  const [title, setTitle] = useState(script?.title ?? '');
  const [chars, setChars] = useState<Character[]>(script?.characters ?? []);
  const [lines, setLines] = useState<DraftLine[]>(() => (script ? script.lines.map(lineToDraft) : []));
  const [newCharName, setNewCharName] = useState('');
  const [pasteOpen, setPasteOpen] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [shiftText, setShiftText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [library, setLibrary] = useState<LibraryEntry[]>(loadLibrary);
  const [libSelection, setLibSelection] = useState('');
  const [notice, setNotice] = useState<string | null>(null);

  const adoptScript = (s: SkitScript) => {
    const draft = scriptToDraft(s);
    setTitle(draft.title);
    setChars(draft.chars);
    setLines(draft.lines);
    setError(null);
  };

  const importText = (raw: string, sourceName: string) => {
    const trimmed = raw.trim();
    if (!trimmed) return;
    if (trimmed.startsWith('{')) {
      try {
        const parsed: unknown = JSON.parse(trimmed);
        if (looksLikeScript(parsed)) {
          adoptScript(parsed);
          return;
        }
        setError('That JSON does not look like a Serifu script.');
        return;
      } catch {
        setError('Could not parse that JSON file.');
        return;
      }
    }
    const cues = parseCues(trimmed);
    if (cues.length === 0) {
      setError('No subtitle cues found — is that an SRT/VTT/ASS file?');
      return;
    }
    // ASS files sometimes carry speaker names — turn them into characters
    // and pre-assign the lines, so tagging is already done.
    const speakerNames = [...new Set(cues.map((c) => c.name).filter((n): n is string => !!n))];
    const speakerChars: Character[] = speakerNames.map((name, i) => ({
      id: `c${i + 1}`,
      name,
      color: CHAR_COLORS[i % CHAR_COLORS.length] ?? '#7ecbff',
    }));
    const idByName = new Map(speakerChars.map((c) => [c.name, c.id]));
    if (speakerChars.length > 0) setChars(speakerChars);
    setTitle((t) => t || sourceName);
    setLines(
      cues.map((cue) => ({
        key: nextKey(),
        character: (cue.name && idByName.get(cue.name)) || '',
        startText: cue.start.toFixed(1),
        endText: cue.end.toFixed(1),
        text: cue.text,
        translation: '',
      }))
    );
    setNotice(
      speakerChars.length > 0
        ? `imported ${cues.length} lines with ${speakerChars.length} speakers auto-detected`
        : `imported ${cues.length} lines — assign speakers with the dropdowns`
    );
    setError(null);
  };

  const onImportFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    file
      .text()
      .then((text) => importText(text, file.name.replace(/[.][^.]+$/, '')))
      .catch(() => setError('Could not read that file.'));
  };

  const addCharacter = () => {
    const name = newCharName.trim();
    if (!name) return;
    let n = chars.length + 1;
    while (chars.some((c) => c.id === `c${n}`)) n++;
    setChars([
      ...chars,
      { id: `c${n}`, name, color: CHAR_COLORS[chars.length % CHAR_COLORS.length] ?? '#7ecbff' },
    ]);
    setNewCharName('');
  };

  const removeCharacter = (id: string) => {
    setChars(chars.filter((c) => c.id !== id));
    setLines(lines.map((l) => (l.character === id ? { ...l, character: '' } : l)));
  };

  const updateLine = (key: number, patch: Partial<DraftLine>) => {
    setLines((prev) => prev.map((l) => (l.key === key ? { ...l, ...patch } : l)));
  };

  const removeLine = (key: number) => {
    setLines((prev) => prev.filter((l) => l.key !== key));
  };

  const insertLineAfter = (key: number) => {
    setLines((prev) => {
      const i = prev.findIndex((l) => l.key === key);
      const anchor = prev[i];
      const start = (anchor && parseTimeInput(anchor.endText)) ?? 0;
      const fresh: DraftLine = {
        key: nextKey(),
        character: '',
        startText: (start + 0.5).toFixed(1),
        endText: (start + 3).toFixed(1),
        text: '',
        translation: '',
      };
      return [...prev.slice(0, i + 1), fresh, ...prev.slice(i + 1)];
    });
  };

  const addLineAtEnd = () => {
    const last = lines[lines.length - 1];
    const start = (last && parseTimeInput(last.endText)) ?? 0;
    setLines([
      ...lines,
      {
        key: nextKey(),
        character: '',
        startText: (start + 0.5).toFixed(1),
        endText: (start + 3).toFixed(1),
        text: '',
        translation: '',
      },
    ]);
  };

  const applyShift = () => {
    const delta = Number(shiftText);
    if (!Number.isFinite(delta) || delta === 0) return;
    setLines((prev) =>
      prev.map((l) => {
        const start = parseTimeInput(l.startText);
        const end = parseTimeInput(l.endText);
        if (start === null || end === null) return l;
        return {
          ...l,
          startText: Math.max(0, start + delta).toFixed(1),
          endText: Math.max(0, end + delta).toFixed(1),
        };
      })
    );
  };

  const buildScript = (): SkitScript | null => {
    const parsed: ScriptLine[] = [];
    for (const [i, dl] of lines.entries()) {
      if (!dl.text.trim()) continue;
      const start = parseTimeInput(dl.startText);
      const end = parseTimeInput(dl.endText);
      if (start === null || end === null) {
        setError(`Line ${i + 1}: could not parse its time.`);
        return null;
      }
      parsed.push({
        id: `l${i + 1}`,
        character: dl.character || null,
        start,
        end: Math.max(start, end),
        tokens: parseRubyText(dl.text.trim()),
        ...(dl.translation.trim() ? { translation: dl.translation.trim() } : {}),
      });
    }
    if (parsed.length === 0) {
      setError('The script has no lines with text.');
      return null;
    }
    parsed.sort((a, b) => a.start - b.start);
    return { title: title.trim() || 'Untitled scene', characters: chars, lines: parsed };
  };

  const saveCurrentToLibrary = () => {
    const s = buildScript();
    if (!s) return;
    if (saveToLibrary(s)) {
      setLibrary(loadLibrary());
      setNotice(`saved 「${s.title}」 to this browser's library`);
      setError(null);
    } else {
      setError('Could not save — browser storage is full or blocked.');
    }
  };

  const loadFromLibrary = () => {
    const entry = library.find((e) => e.title === libSelection);
    if (!entry) return;
    adoptScript(entry.script);
    setNotice(`loaded 「${entry.title}」 — apply to room when ready`);
  };

  const deleteFromLibrary = () => {
    if (!libSelection) return;
    removeFromLibrary(libSelection);
    setLibrary(loadLibrary());
    setLibSelection('');
  };

  const exportJson = () => {
    const s = buildScript();
    if (!s) return;
    const blob = new Blob([JSON.stringify(s, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(s.title || 'serifu-script').replace(/[^\w　-鿿-]+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const apply = async () => {
    const s = buildScript();
    if (!s) return;
    setBusy(true);
    const res = await actions.loadScript(s);
    setBusy(false);
    if (res.ok) onClose();
    else setError(res.error ?? 'The room rejected the script.');
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>台本エディタ / script editor</h2>
          <button className="chip" onClick={onClose}>
            ✕
          </button>
        </header>

        <div className="editor-tools">
          <input
            className="title-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="scene title"
            maxLength={200}
          />
          <select
            value=""
            onChange={(e) => {
              const scene = DEMO_SCENES[Number(e.target.value)];
              if (scene) adoptScript(scene);
            }}
            title="load a bundled Frieren demo scene"
          >
            <option value="" disabled>
              load demo scene…
            </option>
            {DEMO_SCENES.map((s, i) => (
              <option key={s.title} value={i}>
                {s.title}
              </option>
            ))}
          </select>
          <label className="file-button">
            import .srt / .ass / .vtt / .json
            <input type="file" accept=".srt,.vtt,.ass,.ssa,.json,.txt" onChange={onImportFile} hidden />
          </label>
          <button onClick={() => setPasteOpen((v) => !v)}>
            {pasteOpen ? 'hide paste box' : 'paste subtitles'}
          </button>
          <span className="shift-tool">
            shift all
            <input
              value={shiftText}
              onChange={(e) => setShiftText(e.target.value)}
              placeholder="+1.5"
              size={5}
            />
            s
            <button onClick={applyShift}>apply</button>
          </span>
          <button onClick={exportJson}>export JSON</button>
        </div>

        <div className="editor-library">
          <span className="bar-label">エピソード書庫</span>
          <select value={libSelection} onChange={(e) => setLibSelection(e.target.value)}>
            <option value="">— saved episodes ({library.length}) —</option>
            {library.map((entry) => (
              <option key={entry.title} value={entry.title}>
                {entry.title}
              </option>
            ))}
          </select>
          <button disabled={!libSelection} onClick={loadFromLibrary}>
            load
          </button>
          <button className="mini" disabled={!libSelection} onClick={deleteFromLibrary} title="delete from library">
            ✕
          </button>
          <button onClick={saveCurrentToLibrary}>save current</button>
          {notice && <span className="muted">{notice}</span>}
        </div>

        {pasteOpen && (
          <div className="paste-box">
            <textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder="Paste SRT/VTT/JSON here…"
              rows={6}
            />
            <button
              className="primary"
              onClick={() => {
                importText(pasteText, 'pasted subtitles');
                setPasteText('');
                setPasteOpen(false);
              }}
            >
              parse
            </button>
          </div>
        )}

        <div className="editor-chars">
          <span className="bar-label">配役</span>
          {chars.map((c) => (
            <span key={c.id} className="char-pill editor" style={{ borderColor: c.color }}>
              <span style={{ color: c.color }}>{c.name}</span>
              <button className="mini" onClick={() => removeCharacter(c.id)} title="remove">
                ✕
              </button>
            </span>
          ))}
          <input
            value={newCharName}
            onChange={(e) => setNewCharName(e.target.value)}
            placeholder="new character name"
            maxLength={64}
            onKeyDown={(e) => {
              if (e.key === 'Enter') addCharacter();
            }}
          />
          <button onClick={addCharacter}>＋ add</button>
        </div>

        <p className="editor-hint">
          Furigana notation: <code>漢字《かんじ》</code> attaches a reading to the kanji before it;
          use <code>｜</code> to mark the base explicitly, e.g. <code>｜今日《きょう》</code>.
          Times are in seconds (<code>83.5</code>) or <code>m:ss</code>.
        </p>

        <div className="editor-lines">
          {lines.map((l, i) => (
            <div key={l.key} className="editor-line">
              <span className="line-index">{i + 1}</span>
              <select
                value={l.character}
                onChange={(e) => updateLine(l.key, { character: e.target.value })}
              >
                <option value="">— 話者 —</option>
                {chars.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              <input
                className="time-input"
                value={l.startText}
                onChange={(e) => updateLine(l.key, { startText: e.target.value })}
                title="start (seconds or m:ss)"
              />
              <input
                className="time-input"
                value={l.endText}
                onChange={(e) => updateLine(l.key, { endText: e.target.value })}
                title="end"
              />
              <input
                className="text-input"
                value={l.text}
                onChange={(e) => updateLine(l.key, { text: e.target.value })}
                placeholder="セリフ（漢字《かんじ》でふりがな）"
              />
              <input
                className="translation-input"
                value={l.translation}
                onChange={(e) => updateLine(l.key, { translation: e.target.value })}
                placeholder="English translation (optional)"
              />
              <button className="mini" onClick={() => insertLineAfter(l.key)} title="insert line below">
                ＋
              </button>
              <button className="mini" onClick={() => removeLine(l.key)} title="delete line">
                ✕
              </button>
            </div>
          ))}
          <button onClick={addLineAtEnd}>＋ add line</button>
        </div>

        <footer className="modal-footer">
          {error && <span className="error">{error}</span>}
          <div className="spacer" />
          <button onClick={onClose}>cancel</button>
          <button className="primary" disabled={busy} onClick={() => void apply()}>
            {busy ? 'sending…' : 'apply to room'}
          </button>
        </footer>
      </div>
    </div>
  );
}
