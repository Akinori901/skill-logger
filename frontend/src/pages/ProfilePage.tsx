import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import {
  Alert,
  Box,
  Button,
  Divider,
  Grid,
  IconButton,
  Paper,
  Snackbar,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import { useEffect, useState } from "react";
import { generationApi } from "../api/generation";
import { useAiConfig } from "../hooks/useGeneration";
import { useProfile, useSaveProfile } from "../hooks/useProfile";
import type { AiUsageItem, UserProfile } from "../types/careers";

type NarrativeKind = "summary" | "strengths" | "good_at";

const EMPTY: UserProfile = {
  display_name: "",
  age_range: "",
  residence: "",
  headline: "",
  summary: "",
  strengths: "",
  good_at: "",
  ai_usage: [],
};

export default function ProfilePage() {
  const { data } = useProfile();
  const { data: aiConfig } = useAiConfig();
  const save = useSaveProfile();
  const [form, setForm] = useState<UserProfile>(EMPTY);
  const [saved, setSaved] = useState(false);
  const [genKind, setGenKind] = useState<NarrativeKind | null>(null);
  const [genError, setGenError] = useState<string | null>(null);

  // GET は漏洩防止で api_key を返さず has_api_key(bool) を返すため、判定は has_api_key を見る。
  const aiReady = Boolean(aiConfig?.is_enabled && aiConfig?.has_api_key);

  useEffect(() => {
    if (data) setForm({ ...EMPTY, ...data });
  }, [data]);

  const set = <K extends keyof UserProfile>(key: K, value: UserProfile[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const generate = async (kind: NarrativeKind) => {
    setGenError(null);
    setGenKind(kind);
    try {
      const text = await generationApi.generateProfileNarrative(kind, false);
      set(kind, text);
    } catch (e) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "生成に失敗しました。AI設定を確認してください。";
      setGenError(detail);
    } finally {
      setGenKind(null);
    }
  };

  const addAiUsage = () =>
    set("ai_usage", [...(form.ai_usage ?? []), { tool: "", how: "", effect: "" }]);
  const updateAiUsage = (i: number, patch: Partial<AiUsageItem>) =>
    set("ai_usage", (form.ai_usage ?? []).map((u, idx) => (idx === i ? { ...u, ...patch } : u)));
  const removeAiUsage = (i: number) =>
    set("ai_usage", (form.ai_usage ?? []).filter((_, idx) => idx !== i));

  const handleSave = async () => {
    await save.mutateAsync(form);
    setSaved(true);
  };

  return (
    <Box sx={{ maxWidth: 900, mx: "auto" }}>
      <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          プロフィール（職務経歴書サマリ）
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Button variant="contained" onClick={handleSave} disabled={save.isPending}>
          {save.isPending ? "保存中..." : "保存"}
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 2 }}>
        ここで入力した内容は職務経歴書PDFの1ページ目（サマリ）に反映されます。
        要約・自己PRなどの文章は後で「Geminiで生成」できるようになります。
      </Alert>

      {/* 基本情報（事実） */}
      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
          基本情報
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              label="氏名"
              value={form.display_name ?? ""}
              onChange={(e) => set("display_name", e.target.value)}
              fullWidth
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              label="年代"
              value={form.age_range ?? ""}
              onChange={(e) => set("age_range", e.target.value)}
              fullWidth
              placeholder="40代"
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              label="居住地"
              value={form.residence ?? ""}
              onChange={(e) => set("residence", e.target.value)}
              fullWidth
              placeholder="例: 東京都"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="希望ポジション / 肩書"
              value={form.headline ?? ""}
              onChange={(e) => set("headline", e.target.value)}
              fullWidth
              placeholder="バックエンドエンジニア / テックリード"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* 職務要約・自己PR（作文） */}
      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
          職務要約・自己PR（Geminiで生成できます）
        </Typography>
        {!aiReady && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            AIで文章を生成するには、右上のアカウントメニュー →「AI設定」でGeminiのAPIキーを登録してください。
          </Alert>
        )}
        {genError && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setGenError(null)}>
            {genError}
          </Alert>
        )}
        <Stack spacing={2}>
          <Box>
            <TextField
              label="職務要約"
              value={form.summary ?? ""}
              onChange={(e) => set("summary", e.target.value)}
              fullWidth
              multiline
              minRows={3}
            />
            <Button
              startIcon={<AutoAwesomeIcon />}
              size="small"
              sx={{ mt: 0.5 }}
              disabled={!aiReady || genKind !== null}
              onClick={() => generate("summary")}
            >
              {genKind === "summary" ? "生成中..." : "Geminiで生成"}
            </Button>
          </Box>
          <Box>
            <TextField
              label="自己PR：強み"
              value={form.strengths ?? ""}
              onChange={(e) => set("strengths", e.target.value)}
              fullWidth
              multiline
              minRows={2}
            />
            <Button
              startIcon={<AutoAwesomeIcon />}
              size="small"
              sx={{ mt: 0.5 }}
              disabled={!aiReady || genKind !== null}
              onClick={() => generate("strengths")}
            >
              {genKind === "strengths" ? "生成中..." : "Geminiで生成"}
            </Button>
          </Box>
          <Box>
            <TextField
              label="自己PR：得意業務"
              value={form.good_at ?? ""}
              onChange={(e) => set("good_at", e.target.value)}
              fullWidth
              multiline
              minRows={2}
            />
            <Button
              startIcon={<AutoAwesomeIcon />}
              size="small"
              sx={{ mt: 0.5 }}
              disabled={!aiReady || genKind !== null}
              onClick={() => generate("good_at")}
            >
              {genKind === "good_at" ? "生成中..." : "Geminiで生成"}
            </Button>
          </Box>
        </Stack>
      </Paper>

      {/* 生成AI活用 */}
      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
            生成AI活用
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Button startIcon={<AddIcon />} size="small" onClick={addAiUsage}>
            項目を追加
          </Button>
        </Box>
        <Stack spacing={1}>
          {(form.ai_usage ?? []).map((u, i) => (
            <Grid container spacing={1} key={i} sx={{ alignItems: "center" }}>
              <Grid item xs={12} sm={3}>
                <TextField
                  label="ツール"
                  value={u.tool}
                  onChange={(e) => updateAiUsage(i, { tool: e.target.value })}
                  fullWidth
                  size="small"
                  placeholder="ClaudeCode"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="組み込み方"
                  value={u.how}
                  onChange={(e) => updateAiUsage(i, { how: e.target.value })}
                  fullWidth
                  size="small"
                />
              </Grid>
              <Grid item xs={11} sm={4}>
                <TextField
                  label="効果"
                  value={u.effect}
                  onChange={(e) => updateAiUsage(i, { effect: e.target.value })}
                  fullWidth
                  size="small"
                />
              </Grid>
              <Grid item xs={1}>
                <IconButton onClick={() => removeAiUsage(i)} size="small">
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Grid>
            </Grid>
          ))}
          {(form.ai_usage ?? []).length === 0 && (
            <Typography variant="body2" color="text.secondary">
              使用ツール・組み込み方・効果を追加できます。
            </Typography>
          )}
        </Stack>
      </Paper>

      <Divider sx={{ my: 2 }} />
      <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
        <Button variant="contained" onClick={handleSave} disabled={save.isPending}>
          {save.isPending ? "保存中..." : "保存"}
        </Button>
      </Box>

      <Snackbar
        open={saved}
        autoHideDuration={2500}
        onClose={() => setSaved(false)}
        message="プロフィールを保存しました"
      />
    </Box>
  );
}
