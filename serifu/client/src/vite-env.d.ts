/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Buy Me a Coffee / Ko-fi page URL; ☕ links render only when set. */
  readonly VITE_SUPPORT_URL?: string;
  /** Set in the GitHub Pages build: no server, so rooms show a notice. */
  readonly VITE_STATIC_DEMO?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
