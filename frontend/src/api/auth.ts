import { apiClient } from "./client";

interface DjangoUser {
  pk: number;
  username: string;
  email: string;
  is_superuser: boolean;
}

/**
 * 認証関連の Django API クライアント。
 *
 * 認証フロー自体は Amplify SDK が直接 Cognito と通信する。ここに残るのは
 * `getUser` のみで、Django User 情報 (pk / username / email / is_superuser) を
 * 返す `/api/auth/user/` を叩く。バックエンドの `apps.core.views.UserDetailsView`
 * が応答する。
 */
export const authApi = {
  getUser: () => apiClient.get<DjangoUser>("/auth/user/"),
};
