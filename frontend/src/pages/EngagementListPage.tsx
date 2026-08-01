import AddIcon from "@mui/icons-material/Add";
import DescriptionIcon from "@mui/icons-material/Description";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Stack,
  Switch,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { generationApi } from "../api/generation";
import { useDeleteEngagement, useEngagements } from "../hooks/useEngagements";
import type { Engagement } from "../types/careers";
import EngagementEditDialog from "./EngagementEditDialog";

export default function EngagementListPage() {
  const { data: engagements = [], isLoading } = useEngagements();
  const del = useDeleteEngagement();
  const [editing, setEditing] = useState<Engagement | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [anonymize, setAnonymize] = useState(true);

  const openNew = () => {
    setEditing(null);
    setDialogOpen(true);
  };
  const openEdit = (e: Engagement) => {
    setEditing(e);
    setDialogOpen(true);
  };

  const exportMd = async () => {
    const md = await generationApi.exportMarkdown();
    setMarkdown(md);
  };

  const exportPdf = async () => {
    setPdfLoading(true);
    try {
      const blob = await generationApi.exportPdf(undefined, anonymize);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "スキルシート.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          業務経歴の棚卸し
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Button startIcon={<DescriptionIcon />} onClick={exportMd} sx={{ mr: 1 }}>
          Markdown出力
        </Button>
        <FormControlLabel
          control={<Switch size="small" checked={anonymize} onChange={(e) => setAnonymize(e.target.checked)} />}
          label="企業名を伏せる"
          sx={{ mr: 1 }}
        />
        <Button
          startIcon={<PictureAsPdfIcon />}
          onClick={exportPdf}
          disabled={pdfLoading}
          sx={{ mr: 1 }}
        >
          {pdfLoading ? "PDF生成中..." : "PDF出力"}
        </Button>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openNew}>
          案件を追加
        </Button>
      </Box>

      {isLoading && <Typography>読み込み中...</Typography>}
      {!isLoading && engagements.length === 0 && (
        <Typography color="text.secondary">
          まだ案件がありません。「案件を追加」から棚卸しを始めましょう。
        </Typography>
      )}

      <Stack spacing={2}>
        {engagements.map((e) => (
          <Card key={e.id} variant="outlined">
            <CardContent>
              <Typography variant="h6">
                {e.title}
                {e.industry && (
                  <Typography component="span" color="text.secondary" sx={{ ml: 1 }}>
                    （{e.industry}）
                  </Typography>
                )}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {e.company_name} {e.period_start && `｜${e.period_start}〜${e.period_end || "現在"}`}{" "}
                {e.position && `｜${e.position}`}
              </Typography>
              {e.overview && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {e.overview}
                </Typography>
              )}
              <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 1, gap: 0.5 }}>
                {(e.tech_stack ?? []).map((t) => (
                  <Chip key={t} label={t} size="small" />
                ))}
              </Stack>
              {(e.achievements ?? []).length > 0 && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                  成果 {(e.achievements ?? []).length}件 ／ 領域 {(e.domain_links ?? []).length}件 ／
                  URL {(e.urls ?? []).length}件
                </Typography>
              )}
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => openEdit(e)}>
                編集
              </Button>
              <Button
                size="small"
                color="error"
                onClick={() => e.id && del.mutate(e.id)}
              >
                削除
              </Button>
            </CardActions>
          </Card>
        ))}
      </Stack>

      <EngagementEditDialog
        open={dialogOpen}
        engagement={editing}
        onClose={() => setDialogOpen(false)}
      />

      <Dialog open={markdown !== null} onClose={() => setMarkdown(null)} maxWidth="md" fullWidth>
        <DialogTitle>棚卸し Markdown</DialogTitle>
        <DialogContent>
          <Button
            size="small"
            sx={{ mb: 1 }}
            onClick={() => markdown && navigator.clipboard.writeText(markdown)}
          >
            クリップボードにコピー
          </Button>
          <Box
            component="pre"
            sx={{
              whiteSpace: "pre-wrap",
              fontFamily: "monospace",
              fontSize: 13,
              bgcolor: "grey.100",
              p: 2,
              borderRadius: 1,
            }}
          >
            {markdown}
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
}
