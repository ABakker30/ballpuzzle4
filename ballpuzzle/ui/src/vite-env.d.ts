/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_STATUS_URL: string
  readonly VITE_STATUS_INTERVAL_MS: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
