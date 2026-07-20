import type { RoomUser, SkitScript } from '../../../shared/types';
import type { RoomActions } from '../lib/useRoom';

interface Props {
  script: SkitScript | null;
  claims: Record<string, string>;
  users: RoomUser[];
  selfId: string;
  rehearsalEnabled: boolean;
  passScore: number;
  actions: RoomActions;
  onOpenEditor: () => void;
}

const STRICTNESS_PRESETS = [
  { score: 55, label: 'ゆるめ 55+' },
  { score: 70, label: 'ふつう 70+' },
  { score: 85, label: 'きびしめ 85+' },
];

export default function CharacterBar({
  script,
  claims,
  users,
  selfId,
  rehearsalEnabled,
  passScore,
  actions,
  onOpenEditor,
}: Props) {
  if (!script) {
    return (
      <div className="character-bar">
        <span className="muted">配役はここ — characters appear here once a script is loaded.</span>
        <button className="chip" onClick={onOpenEditor}>
          台本 ✎
        </button>
      </div>
    );
  }

  const userById = new Map(users.map((u) => [u.id, u]));

  return (
    <div className="character-bar">
      <span className="bar-label">配役</span>
      {script.characters.map((c) => {
        const ownerId = claims[c.id];
        const owner = ownerId !== undefined ? userById.get(ownerId) : undefined;
        const mine = ownerId === selfId;
        const classes = ['char-pill', ownerId ? 'claimed' : '', mine ? 'mine' : '']
          .filter(Boolean)
          .join(' ');
        return (
          <button
            key={c.id}
            className={classes}
            style={{ borderColor: c.color }}
            disabled={ownerId !== undefined && !mine}
            onClick={() => {
              if (mine) actions.release(c.id);
              else if (ownerId === undefined) actions.claim(c.id);
            }}
            title={
              mine
                ? 'click to release this role'
                : owner
                  ? `played by ${owner.name}`
                  : 'click to claim this role'
            }
          >
            <span className="char-pill-name" style={{ color: c.color }}>
              {c.name}
            </span>
            <small>{mine ? 'あなた ✕' : owner ? owner.name : 'claim'}</small>
          </button>
        );
      })}
      <label className="toggle rehearsal-toggle" title="Auto-pause the video at the start of every claimed line so its actor can say it first.">
        <input
          type="checkbox"
          checked={rehearsalEnabled}
          onChange={(e) => actions.setRehearsal(e.target.checked)}
        />
        セリフで自動停止
      </label>
      <label className="toggle" title="Speech score needed to pass and auto-resume — shared by the whole room.">
        判定
        <select
          value={passScore}
          onChange={(e) => actions.setPassScore(Number(e.target.value))}
        >
          {STRICTNESS_PRESETS.map((p) => (
            <option key={p.score} value={p.score}>
              {p.label}
            </option>
          ))}
          {!STRICTNESS_PRESETS.some((p) => p.score === passScore) && (
            <option value={passScore}>{passScore}+</option>
          )}
        </select>
      </label>
    </div>
  );
}
