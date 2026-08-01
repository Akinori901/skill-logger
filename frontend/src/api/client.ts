/**
 * バックエンド API への axios クライアント。
 *
 * 認証は Cognito (Amplify) 経由。`fetchAuthSession()` から id token を取得して
 * Authorization ヘッダに付与する。
 *
 * **なぜ access token ではなく id token か**:
 * Cognito の access token には email claim が含まれない (デフォルト仕様)。
 * バックエンドの JIT provisioning が m_user_allowed_emails との照合に email を
 * 必要とするため、email を含む id token を送る。バックエンドは JWKS で署名検証
 * + iss / client_id / token_use を全て検証しているのでセキュリティ的には同等。
 *
 * 401 ハンドリング: Amplify が token refresh まで自動で行うため、401 が出た
 * 時点で refresh も失敗している → `signOut()` してログイン画面に戻す。
 */
import { fetchAuthSession, signOut } from "aws-amplify/auth";
import axios, { type InternalAxiosRequestConfig } from "axios";

// バックエンド API のベース URL（.env の VITE_API_BASE_URL）。
// 未設定時はローカルの既定ポート（BACKEND_PORT=19000）。
const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:19000";

export const apiClient = axios.create({
  baseURL: `${baseURL}/api`,
  headers: { "Content-Type": "application/json" },
});

async function getAuthToken(): Promise<string | null> {
  try {
    const session = await fetchAuthSession();
    return session.tokens?.idToken?.toString() ?? null;
  } catch {
    return null;
  }
}

// Request interceptor: Cognito id token を Authorization に付与
apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const token = await getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: 401 → signOut() + /login
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }
    // 未認証で叩いた素直な 401 はそのまま reject
    const token = await getAuthToken();
    if (!token) {
      return Promise.reject(error);
    }
    // session があるのに 401 = Amplify の自動 refresh も失敗 → signOut + /login
    // (Hub の signedOut event で authStore もクリアされる)
    try {
      await signOut();
    } catch {
      // signOut 失敗時も login へリダイレクト
    }
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);
