import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import LaunchIcon from "@mui/icons-material/Launch";
import { AppBar, Box, Button, IconButton, Menu, MenuItem, Toolbar, Typography } from "@mui/material";
import { signOut } from "aws-amplify/auth";
import { useState } from "react";
import { Link as RouterLink, useLocation, useNavigate } from "react-router-dom";

import { useAuthStore } from "../stores/authStore";
import AiConfigDialog from "../pages/AiConfigDialog";

/**
 * 横断アプリリンク。
 * .env の VITE_APP_LINKS に "ラベル|URL" のカンマ区切りで別アプリを登録すると、
 * ヘッダー右側にそのアプリへのリンクが表示される（将来のマルチアプリ横断操作用）。
 * 例: VITE_APP_LINKS=app-one|http://localhost:8888,app-two|http://localhost:8080
 */
function parseAppLinks(): { label: string; url: string }[] {
  const raw = import.meta.env.VITE_APP_LINKS as string | undefined;
  if (!raw) return [];
  return raw
    .split(",")
    .map((pair) => pair.trim())
    .filter(Boolean)
    .map((pair) => {
      const [label, url] = pair.split("|");
      return { label: (label ?? "").trim(), url: (url ?? "").trim() };
    })
    .filter((l) => l.label && l.url);
}

const NAV = [
  { to: "/engagements", label: "棚卸し" },
  { to: "/profile", label: "プロフィール" },
  { to: "/import", label: "取り込み" },
  { to: "/expert-application", label: "Expert申請文" },
];

export default function AppHeader() {
  const location = useLocation();
  const navigate = useNavigate();
  const appLinks = parseAppLinks();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [aiConfigOpen, setAiConfigOpen] = useState(false);

  const openAiConfig = () => {
    setAnchorEl(null);
    setAiConfigOpen(true);
  };

  const handleLogout = async () => {
    setAnchorEl(null);
    // Cognito signOut。Hosted UI の logout URL 経由で /login に戻り、
    // Hub.signedOut event で authStore もクリアされる。失敗時はフォールバック。
    try {
      await signOut();
    } catch {
      logout();
      navigate("/login");
    }
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" sx={{ fontWeight: 700, mr: 3 }}>
          SkillLogger
        </Typography>
        {NAV.map((n) => (
          <Button
            key={n.to}
            component={RouterLink}
            to={n.to}
            color="inherit"
            sx={{ fontWeight: location.pathname === n.to ? 700 : 400 }}
          >
            {n.label}
          </Button>
        ))}
        <Box sx={{ flexGrow: 1 }} />
        {appLinks.map((l) => (
          <Button
            key={l.url}
            href={l.url}
            target="_blank"
            rel="noopener"
            color="inherit"
            size="small"
            endIcon={<LaunchIcon fontSize="small" />}
            sx={{ opacity: 0.85 }}
          >
            {l.label}
          </Button>
        ))}
        {user && (
          <>
            <Typography variant="body2" sx={{ ml: 2, mr: 0.5 }}>
              {user.username}
              {user.is_superuser && "（管理者）"}
            </Typography>
            <IconButton
              color="inherit"
              aria-label="アカウントメニュー"
              onClick={(e) => setAnchorEl(e.currentTarget)}
            >
              <AccountCircleIcon />
            </IconButton>
            <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
              <MenuItem onClick={openAiConfig}>AI設定</MenuItem>
              <MenuItem onClick={handleLogout}>ログアウト</MenuItem>
            </Menu>
          </>
        )}
      </Toolbar>
      <AiConfigDialog open={aiConfigOpen} onClose={() => setAiConfigOpen(false)} />
    </AppBar>
  );
}
