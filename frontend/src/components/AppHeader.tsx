import LaunchIcon from "@mui/icons-material/Launch";
import { AppBar, Box, Button, Toolbar, Typography } from "@mui/material";
import { Link as RouterLink, useLocation } from "react-router-dom";

/**
 * 横断アプリリンク。
 * .env の VITE_APP_LINKS に "ラベル|URL" のカンマ区切りで別アプリを登録すると、
 * ヘッダー右側にそのアプリへのリンクが表示される（将来のマルチアプリ横断操作用）。
 * 例: VITE_APP_LINKS=money-pilot|http://localhost:8888,fair-value|http://localhost:8080
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
  { to: "/import", label: "取り込み" },
  { to: "/expert-application", label: "Expert申請文" },
];

export default function AppHeader() {
  const location = useLocation();
  const appLinks = parseAppLinks();

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
      </Toolbar>
    </AppBar>
  );
}
