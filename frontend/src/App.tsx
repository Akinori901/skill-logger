import { Container } from "@mui/material";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import AppHeader from "./components/AppHeader";
import ProtectedRoute from "./components/common/ProtectedRoute";
import AuthCallbackPage from "./pages/AuthCallbackPage";
import EngagementListPage from "./pages/EngagementListPage";
import ExpertApplicationPage from "./pages/ExpertApplicationPage";
import ImportPage from "./pages/ImportPage";
import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";

/** ヘッダー付きの保護レイアウト（ログイン必須ページ共通の外枠）。 */
function ProtectedLayout() {
  return (
    <>
      <AppHeader />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Outlet />
      </Container>
    </>
  );
}

export default function App() {
  return (
    <Routes>
      {/* 認証外（ProtectedRoute の外に置く。callback は isAuthenticated=false の段階で
          到達するため、内側に置くと即 /login に飛んでしまう）。 */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />

      {/* 認証必須 */}
      <Route element={<ProtectedRoute />}>
        <Route element={<ProtectedLayout />}>
          <Route path="/" element={<Navigate to="/engagements" replace />} />
          <Route path="/engagements" element={<EngagementListPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/import" element={<ImportPage />} />
          <Route path="/expert-application" element={<ExpertApplicationPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
