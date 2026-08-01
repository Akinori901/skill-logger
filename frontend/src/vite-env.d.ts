/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_APP_LINKS?: string;
  // Cognito 認証（共通基盤 qol-user-pool）。qol-user-pool の terraform output より。
  readonly VITE_COGNITO_USER_POOL_ID?: string;
  readonly VITE_COGNITO_WEB_CLIENT_ID?: string;
  readonly VITE_COGNITO_DOMAIN_PREFIX?: string;
  readonly VITE_COGNITO_REGION?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
