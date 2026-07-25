import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import {
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useSaveEngagement, useSupportDomains } from "../hooks/useEngagements";
import {
  ACHIEVEMENT_CATEGORY_LABELS,
  type Achievement,
  type AchievementCategory,
  type Engagement,
  type EngagementDomainLink,
  type EngagementUrl,
} from "../types/careers";

interface Props {
  open: boolean;
  engagement: Engagement | null;
  onClose: () => void;
}

const EMPTY: Engagement = {
  title: "",
  industry: "",
  company_name: "",
  period_start: "",
  period_end: "",
  position: "",
  overview: "",
  responsibilities: "",
  challenges: "",
  tech_stack: [],
  achievements: [],
  urls: [],
  domain_links: [],
  is_public: false,
};

export default function EngagementEditDialog({ open, engagement, onClose }: Props) {
  const { data: domains = [] } = useSupportDomains();
  const save = useSaveEngagement();
  const [form, setForm] = useState<Engagement>(EMPTY);
  const [techInput, setTechInput] = useState("");

  useEffect(() => {
    setForm(engagement ? { ...EMPTY, ...engagement } : EMPTY);
    setTechInput("");
  }, [engagement, open]);

  const set = <K extends keyof Engagement>(key: K, value: Engagement[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const addTech = () => {
    const v = techInput.trim();
    if (v && !(form.tech_stack ?? []).includes(v)) {
      set("tech_stack", [...(form.tech_stack ?? []), v]);
    }
    setTechInput("");
  };

  const addAchievement = () =>
    set("achievements", [
      ...(form.achievements ?? []),
      { category: "quality" as AchievementCategory, description: "" },
    ]);

  const updateAchievement = (i: number, patch: Partial<Achievement>) =>
    set(
      "achievements",
      (form.achievements ?? []).map((a, idx) => (idx === i ? { ...a, ...patch } : a)),
    );

  const removeAchievement = (i: number) =>
    set("achievements", (form.achievements ?? []).filter((_, idx) => idx !== i));

  const addUrl = () => set("urls", [...(form.urls ?? []), { url: "", label: "" }]);
  const updateUrl = (i: number, patch: Partial<EngagementUrl>) =>
    set("urls", (form.urls ?? []).map((u, idx) => (idx === i ? { ...u, ...patch } : u)));
  const removeUrl = (i: number) => set("urls", (form.urls ?? []).filter((_, idx) => idx !== i));

  const toggleDomain = (domainId: number) => {
    const links = form.domain_links ?? [];
    const exists = links.find((l) => l.support_domain_id === domainId);
    if (exists) {
      set("domain_links", links.filter((l) => l.support_domain_id !== domainId));
    } else {
      const link: EngagementDomainLink = { support_domain_id: domainId, relevance: 3 };
      set("domain_links", [...links, link]);
    }
  };

  const setRelevance = (domainId: number, relevance: number) =>
    set(
      "domain_links",
      (form.domain_links ?? []).map((l) =>
        l.support_domain_id === domainId ? { ...l, relevance } : l,
      ),
    );

  const handleSave = async () => {
    await save.mutateAsync(form);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{form.id ? "案件を編集" : "案件を追加"}</DialogTitle>
      <DialogContent dividers>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              label="案件名（仮名でOK）"
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
              fullWidth
              required
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              label="業界"
              value={form.industry}
              onChange={(e) => set("industry", e.target.value)}
              fullWidth
              placeholder="SaaS / 製造 / 金融 など"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              label="会社名（任意）"
              value={form.company_name}
              onChange={(e) => set("company_name", e.target.value)}
              fullWidth
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              label="従業員数"
              type="number"
              value={form.company_size_employees ?? ""}
              onChange={(e) =>
                set("company_size_employees", e.target.value ? Number(e.target.value) : null)
              }
              fullWidth
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              label="開発組織人数"
              type="number"
              value={form.dev_org_size ?? ""}
              onChange={(e) => set("dev_org_size", e.target.value ? Number(e.target.value) : null)}
              fullWidth
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              label="開始 (YYYY-MM)"
              value={form.period_start}
              onChange={(e) => set("period_start", e.target.value)}
              fullWidth
              placeholder="2024-04"
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              label="終了 (空=現在)"
              value={form.period_end}
              onChange={(e) => set("period_end", e.target.value)}
              fullWidth
              placeholder="2025-03"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="ポジション"
              value={form.position}
              onChange={(e) => set("position", e.target.value)}
              fullWidth
              placeholder="テックリード / PM補佐 など"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="プロジェクト概要"
              value={form.overview}
              onChange={(e) => set("overview", e.target.value)}
              fullWidth
              multiline
              minRows={2}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="担当したこと"
              value={form.responsibilities}
              onChange={(e) => set("responsibilities", e.target.value)}
              fullWidth
              multiline
              minRows={2}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="苦労したこと・工夫したこと"
              value={form.challenges}
              onChange={(e) => set("challenges", e.target.value)}
              fullWidth
              multiline
              minRows={2}
            />
          </Grid>

          {/* 技術スタック（タグ入力） */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>
              技術スタック
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 1, gap: 1 }}>
              {(form.tech_stack ?? []).map((t) => (
                <Chip
                  key={t}
                  label={t}
                  onDelete={() =>
                    set("tech_stack", (form.tech_stack ?? []).filter((x) => x !== t))
                  }
                />
              ))}
            </Stack>
            <TextField
              label="技術を追加（Enter）"
              value={techInput}
              onChange={(e) => setTechInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addTech();
                }
              }}
              size="small"
              placeholder="AWS / Laravel / Vue など"
            />
          </Grid>

          {/* 成果（数字付き） */}
          <Grid item xs={12}>
            <Divider sx={{ mb: 1 }} />
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <Typography variant="subtitle2">成果（数字があると生成精度UP）</Typography>
              <Button startIcon={<AddIcon />} size="small" onClick={addAchievement}>
                成果を追加
              </Button>
            </Box>
            {(form.achievements ?? []).map((a, i) => (
              <Grid container spacing={1} key={i} sx={{ mt: 0.5, alignItems: "center" }}>
                <Grid item xs={6} sm={2}>
                  <TextField
                    select
                    label="区分"
                    value={a.category}
                    onChange={(e) =>
                      updateAchievement(i, { category: e.target.value as AchievementCategory })
                    }
                    fullWidth
                    size="small"
                  >
                    {Object.entries(ACHIEVEMENT_CATEGORY_LABELS).map(([k, v]) => (
                      <MenuItem key={k} value={k}>
                        {v}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid item xs={6} sm={4}>
                  <TextField
                    label="内容"
                    value={a.description}
                    onChange={(e) => updateAchievement(i, { description: e.target.value })}
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={4} sm={1.5}>
                  <TextField
                    label="改善前"
                    value={a.metric_before ?? ""}
                    onChange={(e) => updateAchievement(i, { metric_before: e.target.value })}
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={4} sm={1.5}>
                  <TextField
                    label="改善後"
                    value={a.metric_after ?? ""}
                    onChange={(e) => updateAchievement(i, { metric_after: e.target.value })}
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={3} sm={2}>
                  <TextField
                    label="単位"
                    value={a.metric_unit ?? ""}
                    onChange={(e) => updateAchievement(i, { metric_unit: e.target.value })}
                    fullWidth
                    size="small"
                    placeholder="時間/円/件"
                  />
                </Grid>
                <Grid item xs={1} sm={1}>
                  <IconButton onClick={() => removeAchievement(i)} size="small">
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Grid>
              </Grid>
            ))}
          </Grid>

          {/* 支援領域の紐付け */}
          <Grid item xs={12}>
            <Divider sx={{ mb: 1 }} />
            <Typography variant="subtitle2" gutterBottom>
              関連する支援領域（Expert申請の生成に使用）
            </Typography>
            <Grid container spacing={0.5}>
              {domains.map((d) => {
                const link = (form.domain_links ?? []).find((l) => l.support_domain_id === d.id);
                const checked = !!link;
                return (
                  <Grid item xs={12} sm={6} key={d.id}>
                    <Box sx={{ display: "flex", alignItems: "center" }}>
                      <FormControlLabel
                        control={
                          <Checkbox checked={checked} onChange={() => toggleDomain(d.id)} />
                        }
                        label={d.name}
                      />
                      {checked && (
                        <TextField
                          select
                          size="small"
                          label="寄与度"
                          value={link!.relevance}
                          onChange={(e) => setRelevance(d.id, Number(e.target.value))}
                          sx={{ width: 90, ml: "auto" }}
                        >
                          {[1, 2, 3, 4, 5].map((n) => (
                            <MenuItem key={n} value={n}>
                              {n}
                            </MenuItem>
                          ))}
                        </TextField>
                      )}
                    </Box>
                  </Grid>
                );
              })}
            </Grid>
          </Grid>

          {/* 実績URL */}
          <Grid item xs={12}>
            <Divider sx={{ mb: 1 }} />
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <Typography variant="subtitle2">実績URL</Typography>
              <Button startIcon={<AddIcon />} size="small" onClick={addUrl}>
                URLを追加
              </Button>
            </Box>
            {(form.urls ?? []).map((u, i) => (
              <Grid container spacing={1} key={i} sx={{ mt: 0.5, alignItems: "center" }}>
                <Grid item xs={4} sm={3}>
                  <TextField
                    label="ラベル"
                    value={u.label ?? ""}
                    onChange={(e) => updateUrl(i, { label: e.target.value })}
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={7} sm={8}>
                  <TextField
                    label="URL"
                    value={u.url}
                    onChange={(e) => updateUrl(i, { url: e.target.value })}
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={1}>
                  <IconButton onClick={() => removeUrl(i)} size="small">
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Grid>
              </Grid>
            ))}
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>キャンセル</Button>
        <Button variant="contained" onClick={handleSave} disabled={!form.title || save.isPending}>
          保存
        </Button>
      </DialogActions>
    </Dialog>
  );
}
