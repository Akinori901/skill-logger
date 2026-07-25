import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Alert,
  Box,
  Button,
  Chip,
  FormControlLabel,
  MenuItem,
  Paper,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { importApi, type ImportResult } from "../api/careers";

const DECISION_OPTIONS = [
  { value: "", label: "すべて取り込む" },
  { value: "as_is", label: "as_is（自社帰属）のみ" },
  { value: "anonymize", label: "anonymize のみ" },
  { value: "metadata_only", label: "metadata_only のみ" },
];

export default function ImportPage() {
  const qc = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [onlyDecision, setOnlyDecision] = useState("");
  const [result, setResult] = useState<ImportResult | null>(null);
  const [isPreview, setIsPreview] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (dryRun: boolean) => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const res = await importApi.upload(file, onlyDecision, dryRun);
      setResult(res);
      setIsPreview(dryRun);
      if (!dryRun) qc.invalidateQueries({ queryKey: ["engagements"] });
    } catch (e) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "取り込みに失敗しました。feed の形式を確認してください。";
      setError(detail);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
        棚卸しデータの取り込み
      </Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        skill-inventory で書き出した <code>skilllogger-feed.json</code> をアップロードすると、
        技術メタデータ（言語・FW・期間・規模・関与コミット）が案件の下書きとして登録されます。
        業界・成果・支援領域は取り込み後にご自身で補ってください。
      </Alert>

      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Stack spacing={2}>
          <Button
            component="label"
            variant="outlined"
            startIcon={<UploadFileIcon />}
            sx={{ alignSelf: "flex-start" }}
          >
            {file ? file.name : "feed.json を選択"}
            <input
              type="file"
              accept="application/json,.json"
              hidden
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setResult(null);
              }}
            />
          </Button>

          <TextField
            select
            label="取り込む範囲（帰属フィルタ）"
            value={onlyDecision}
            onChange={(e) => setOnlyDecision(e.target.value)}
            sx={{ maxWidth: 320 }}
            size="small"
          >
            {DECISION_OPTIONS.map((o) => (
              <MenuItem key={o.value} value={o.value}>
                {o.label}
              </MenuItem>
            ))}
          </TextField>

          <Box sx={{ display: "flex", gap: 1 }}>
            <Button
              variant="outlined"
              disabled={!file || busy}
              onClick={() => run(true)}
            >
              プレビュー（登録しない）
            </Button>
            <Button
              variant="contained"
              disabled={!file || busy}
              onClick={() => run(false)}
            >
              取り込む
            </Button>
          </Box>
        </Stack>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Paper variant="outlined" sx={{ p: 3 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
            {isPreview ? "プレビュー結果" : "取り込み完了"}
          </Typography>
          <FormControlLabel
            control={<Switch checked disabled />}
            label={`新規 ${result.created_count} / 更新 ${result.updated_count} / スキップ ${result.skipped_count}`}
            sx={{ mb: 2, pointerEvents: "none" }}
          />
          <ResultBlock title="新規" color="success" items={result.created} />
          <ResultBlock title="更新" color="warning" items={result.updated} />
          <ResultBlock title="スキップ（技術データなし/フィルタ対象外）" color="default" items={result.skipped} />
          {isPreview && result.created_count + result.updated_count > 0 && (
            <Alert severity="success" sx={{ mt: 2 }}>
              問題なければ「取り込む」を押して登録してください。
            </Alert>
          )}
        </Paper>
      )}
    </Box>
  );
}

function ResultBlock({
  title,
  color,
  items,
}: {
  title: string;
  color: "success" | "warning" | "default";
  items: string[];
}) {
  if (items.length === 0) return null;
  return (
    <Box sx={{ mb: 1.5 }}>
      <Typography variant="caption" color="text.secondary">
        {title}（{items.length}）
      </Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 0.5, mt: 0.5 }}>
        {items.map((name) => (
          <Chip key={name} label={name} size="small" color={color} variant="outlined" />
        ))}
      </Stack>
    </Box>
  );
}
