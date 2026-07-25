import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import SettingsIcon from "@mui/icons-material/Settings";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useSupportDomains } from "../hooks/useEngagements";
import { useGenerateAll } from "../hooks/useGeneration";
import type { DomainStatement, SupportDomain } from "../types/careers";
import AiConfigDialog from "./AiConfigDialog";

const MAX_SELECTED = 5;
const MIN_CHARS = 50;
const MAX_CHARS = 200;

export default function ExpertApplicationPage() {
  const { data: domains = [] } = useSupportDomains();
  const generateAll = useGenerateAll();
  const [selected, setSelected] = useState<number[]>([]); // support_domain_id を優先順に
  const [statements, setStatements] = useState<Record<number, string>>({});
  const [configOpen, setConfigOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const domainById = useMemo(() => {
    const m: Record<number, SupportDomain> = {};
    domains.forEach((d) => (m[d.id] = d));
    return m;
  }, [domains]);

  const toggle = (id: number) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_SELECTED) return prev;
      return [...prev, id];
    });
  };

  const handleGenerate = async () => {
    setError(null);
    const codes = selected.map((id) => domainById[id]?.code).filter(Boolean) as string[];
    try {
      const results: DomainStatement[] = await generateAll.mutateAsync(codes);
      const next: Record<number, string> = {};
      results.forEach((r) => (next[r.support_domain_id] = r.body));
      setStatements((prev) => ({ ...prev, ...next }));
    } catch (e) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "生成に失敗しました。AI設定を確認してください。";
      setError(detail);
    }
  };

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          Expert 申請文の生成
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Button startIcon={<SettingsIcon />} onClick={() => setConfigOpen(true)}>
          AI設定
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 2 }}>
        バリューを発揮できる支援領域を最大5つ、優先順位の高い順に選んでください（クリックした順が優先順位になります）。
        各領域に紐づけた案件から、50〜200字の申請文を生成します。
      </Alert>

      {/* 領域選択 */}
      <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 1, mb: 2 }}>
        {domains.map((d) => {
          const idx = selected.indexOf(d.id);
          const isSelected = idx >= 0;
          return (
            <Chip
              key={d.id}
              label={isSelected ? `${idx + 1}. ${d.name}` : d.name}
              color={isSelected ? "primary" : "default"}
              variant={isSelected ? "filled" : "outlined"}
              onClick={() => toggle(d.id)}
            />
          );
        })}
      </Stack>

      <Button
        variant="contained"
        startIcon={<AutoAwesomeIcon />}
        onClick={handleGenerate}
        disabled={selected.length === 0 || generateAll.isPending}
        sx={{ mb: 3 }}
      >
        {generateAll.isPending ? "生成中..." : "選択領域の申請文をAI生成"}
      </Button>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* 生成結果（優先順に表示・編集可能） */}
      <Stack spacing={2}>
        {selected.map((id, idx) => {
          const domain = domainById[id];
          const body = statements[id] ?? "";
          const count = body.length;
          const countColor =
            count === 0
              ? "text.secondary"
              : count < MIN_CHARS || count > MAX_CHARS
                ? "error.main"
                : "success.main";
          return (
            <Card key={id} variant="outlined">
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                    {idx + 1}. {domain?.name}
                  </Typography>
                  <Box sx={{ flexGrow: 1 }} />
                  <Typography variant="caption" sx={{ color: countColor, mr: 1 }}>
                    {count} 字（推奨 {MIN_CHARS}〜{MAX_CHARS}）
                  </Typography>
                  <Button
                    size="small"
                    startIcon={<ContentCopyIcon fontSize="small" />}
                    onClick={() => navigator.clipboard.writeText(body)}
                    disabled={!body}
                  >
                    コピー
                  </Button>
                </Box>
                <TextField
                  value={body}
                  onChange={(e) =>
                    setStatements((prev) => ({ ...prev, [id]: e.target.value }))
                  }
                  fullWidth
                  multiline
                  minRows={3}
                  placeholder="「AI生成」で下書きを作成、または直接入力してください。"
                />
              </CardContent>
            </Card>
          );
        })}
      </Stack>

      <AiConfigDialog open={configOpen} onClose={() => setConfigOpen(false)} />
    </Box>
  );
}
