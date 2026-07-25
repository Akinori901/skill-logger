import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  MenuItem,
  Stack,
  Switch,
  TextField,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useAiConfig, useSaveAiConfig } from "../hooks/useGeneration";
import type { AiConfig } from "../types/careers";

interface Props {
  open: boolean;
  onClose: () => void;
}

// Claude のようにプロバイダ→モデル選択で切り替える。既定は無料枠のある Gemini。
const MODEL_PRESETS: Record<AiConfig["provider"], string[]> = {
  gemini: ["gemini-2.5-flash", "gemini-2.5-pro"],
  claude: ["claude-haiku-4-5", "claude-sonnet-5", "claude-opus-4-8"],
  openai: ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
};

const PROVIDER_LABELS: Record<AiConfig["provider"], string> = {
  gemini: "Gemini（無料枠あり・既定）",
  claude: "Claude",
  openai: "OpenAI",
};

export default function AiConfigDialog({ open, onClose }: Props) {
  const { data } = useAiConfig();
  const save = useSaveAiConfig();
  const [form, setForm] = useState<AiConfig>({
    provider: "gemini",
    model: "gemini-2.5-flash",
    is_enabled: false,
    api_key: "",
  });

  useEffect(() => {
    if (data) {
      setForm({
        provider: data.provider,
        model: data.model,
        is_enabled: data.is_enabled,
        api_key: "",
        has_api_key: data.has_api_key,
      });
    }
  }, [data, open]);

  const set = <K extends keyof AiConfig>(k: K, v: AiConfig[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSave = async () => {
    await save.mutateAsync(form);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>AI設定</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Alert severity="info">
            API キーは DB にのみ保存され、リポジトリには含まれません。
          </Alert>
          <TextField
            select
            label="プロバイダ"
            value={form.provider}
            onChange={(e) => {
              const provider = e.target.value as AiConfig["provider"];
              set("provider", provider);
              set("model", MODEL_PRESETS[provider][0]);
            }}
          >
            {(Object.keys(PROVIDER_LABELS) as AiConfig["provider"][]).map((p) => (
              <MenuItem key={p} value={p}>
                {PROVIDER_LABELS[p]}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            label="モデル"
            value={form.model}
            onChange={(e) => set("model", e.target.value)}
          >
            {MODEL_PRESETS[form.provider].map((m) => (
              <MenuItem key={m} value={m}>
                {m}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="API キー"
            type="password"
            value={form.api_key ?? ""}
            onChange={(e) => set("api_key", e.target.value)}
            placeholder={form.has_api_key ? "設定済み（変更する場合のみ入力）" : "sk-..."}
            helperText={form.has_api_key ? "既に登録済みです。空のままなら現在のキーを維持します。" : ""}
          />
          <FormControlLabel
            control={
              <Switch
                checked={form.is_enabled}
                onChange={(e) => set("is_enabled", e.target.checked)}
              />
            }
            label="AI生成を有効にする"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>キャンセル</Button>
        <Button variant="contained" onClick={handleSave} disabled={save.isPending}>
          保存
        </Button>
      </DialogActions>
    </Dialog>
  );
}
