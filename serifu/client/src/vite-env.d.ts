/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Buy Me a Coffee / Ko-fi page URL; ☕ links render only when set. */
  readonly VITE_SUPPORT_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
