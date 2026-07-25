import axios from "axios";

// バックエンド API のベース URL（.env の VITE_API_BASE_URL）。
// 未設定時はローカルの既定ポート（BACKEND_PORT=19000）。
const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:19000";

export const apiClient = axios.create({
  baseURL: `${baseURL}/api`,
  headers: { "Content-Type": "application/json" },
});

// Phase B（共通 Cognito 化）では、ここで interceptor が Cognito の id token を
// Authorization ヘッダーに付与する。MVP は仮認証（サーバ側で固定ユーザー）なので何もしない。
