export type TranslationMode = 'show' | 'hover' | 'hide';

export interface DisplaySettings {
  furigana: boolean;
  translation: TranslationMode;
}

const SETTINGS_KEY = 'serifu:settings';
const NAME_KEY = 'serifu:name';

export const DEFAULT_SETTINGS: DisplaySettings = {
  furigana: true,
  translation: 'hover',
};

export function loadSettings(): DisplaySettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    const parsed = JSON.parse(raw) as Partial<DisplaySettings>;
    return {
      furigana: typeof parsed.furigana === 'boolean' ? parsed.furigana : DEFAULT_SETTINGS.furigana,
      translation:
        parsed.translation === 'show' || parsed.translation === 'hover' || parsed.translation === 'hide'
          ? parsed.translation
          : DEFAULT_SETTINGS.translation,
    };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(settings: DisplaySettings): void {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    // Private-mode storage failures are fine to ignore.
  }
}

export function loadName(): string {
  try {
    return localStorage.getItem(NAME_KEY) ?? '';
  } catch {
    return '';
  }
}

export function saveName(name: string): void {
  try {
    localStorage.setItem(NAME_KEY, name);
  } catch {
    // ignore
  }
}
