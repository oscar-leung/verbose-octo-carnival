import type { RoomState, SkitScript } from '../../../shared/types';
import type { RoomActions } from '../lib/useRoom';
import type { DisplaySettings } from '../lib/settings';
import RubyText from './RubyText';

interface Props {
  script: SkitScript;
  state: RoomState;
  actions: RoomActions;
  settings: DisplaySettings;
}

/** Overlay shown while playback is auto-paused for someone to act a line. */
export default function RehearsalBanner({ script, state, actions, settings }: Props) {
  const lineId = state.playback.pausedForLineId;
  const line = script.lines.find((l) => l.id === lineId);
  if (!line) return null;
  const char = script.characters.find((c) => c.id === line.character);
  const ownerId = line.character !== null ? state.claims[line.character] : undefined;
  const owner = state.users.find((u) => u.id === ownerId);

  return (
    <div className="rehearsal-banner">
      <div className="rb-header">
        🎬 <strong style={{ color: char?.color }}>{char?.name ?? '???'}</strong>
        {owner ? <span> — {owner.name}, your line!</span> : null}
      </div>
      <p className="rb-line">
        <RubyText tokens={line.tokens} furigana={settings.furigana} />
      </p>
      {line.translation && settings.translation !== 'hide' && (
        <p className={settings.translation === 'hover' ? 'rb-translation hover-reveal' : 'rb-translation'}>
          {line.translation}
        </p>
      )}
      <button className="primary" onClick={() => actions.rehearsalResume()}>
        言えた！続ける ▶ <small>(space)</small>
      </button>
    </div>
  );
}
