"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL, apiGet, apiPost, apiPut } from "@/lib/api";
import {
  PageHeader,
  SectionCard,
  PrimaryButton,
  SecondaryButton,
  IconButton,
  Input,
  Textarea,
  Select,
  FormGroup,
  Alert,
  ErrorBanner,
  StatusChip,
  LoadingSkeleton,
  ProgressIndicator,
} from "@/components/ui";
import {
  Home,
  Package,
  RefreshCw,
  Download,
  Trash2,
  X,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
} from "lucide-react";

type ImageJob = {
  id: string;
  state: "queued" | "running" | "cancelled" | "failed" | "succeeded";
  message?: string | null;
  created_at?: number;
  started_at?: number | null;
  finished_at?: number | null;
  image_path?: string | null;
  image_paths?: string[] | null;
  error?: string | null;
  params?: Record<string, unknown> | null;
};

type ImageItem = {
  path: string;
  mtime: number;
  size_bytes: number;
  url: string;
};

export default function GeneratePage() {
  const [prompt, setPrompt] = useState("");
  const [negative, setNegative] = useState("");
  const [seed, setSeed] = useState<string>("");
  const [checkpoint, setCheckpoint] = useState<string>("");
  const [width, setWidth] = useState<string>("1024");
  const [height, setHeight] = useState<string>("1024");
  const [steps, setSteps] = useState<string>("25");
  const [cfg, setCfg] = useState<string>("7.0");
  const [samplerName, setSamplerName] = useState<string>("euler");
  const [scheduler, setScheduler] = useState<string>("normal");
  const [samplers, setSamplers] = useState<string[]>([]);
  const [schedulers, setSchedulers] = useState<string[]>([]);
  const [batchSize, setBatchSize] = useState<string>("1");
  const [comfyStatus, setComfyStatus] = useState<{
    ok: boolean;
    base_url: string;
    base_url_source?: string;
    installed?: boolean;
    running?: boolean;
    reachable?: boolean;
    error?: string;
    message?: string;
    action_required?: "install" | "start" | "wait" | null;
  } | null>(null);
  const [checkpoints, setCheckpoints] = useState<string[]>([]);
  const [comfyBaseUrlInput, setComfyBaseUrlInput] = useState<string>("");
  const [isSavingComfyUrl, setIsSavingComfyUrl] = useState(false);
  const [job, setJob] = useState<ImageJob | null>(null);
  const [jobs, setJobs] = useState<ImageJob[]>([]);
  const [gallery, setGallery] = useState<ImageItem[]>([]);
  const [galleryTotal, setGalleryTotal] = useState<number>(0);
  const [galleryOffset, setGalleryOffset] = useState<number>(0);
  const [galleryLimit, setGalleryLimit] = useState<number>(48);
  const [isLoadingGallery, setIsLoadingGallery] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCancelling, setIsCancelling] = useState<string | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [storage, setStorage] = useState<{
    images_count: number;
    images_bytes: number;
  } | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [isDeletingImage, setIsDeletingImage] = useState<string | null>(null);
  const [galleryQuery, setGalleryQuery] = useState("");
  const [gallerySort, setGallerySort] = useState<"newest" | "oldest" | "name">(
    "newest"
  );
  const [selectedImages, setSelectedImages] = useState<Record<string, boolean>>(
    {}
  );
  const [isBulkDeletingImages, setIsBulkDeletingImages] = useState(false);
  const [cleanupDays, setCleanupDays] = useState<string>("30");
  const [isCleaningUp, setIsCleaningUp] = useState(false);
  const [presets, setPresets] = useState<
    Array<{
      id: string;
      name: string;
      description: string;
      category: string;
      prompt_template?: string | null;
      negative_prompt?: string | null;
      width?: number | null;
      height?: number | null;
      steps?: number | null;
      cfg?: number | null;
      sampler_name?: string | null;
      scheduler?: string | null;
      batch_size?: number | null;
      checkpoint?: string | null;
      post_processing?: {
        face_restoration?: {
          enabled?: boolean;
          method?: string;
          strength?: number;
        };
        upscale?: { enabled?: boolean; method?: string; scale?: number };
        film_grain?: { enabled?: boolean; strength?: number };
        tone_mapping?: { enabled?: boolean; method?: string };
      };
      optimization_notes?: string | null;
    }>
  >([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>("");
  const [isLoadingPresets, setIsLoadingPresets] = useState(false);
  const [pipelinePresets, setPipelinePresets] = useState<
    Array<{
      id: string;
      name: string;
      description: string;
      category: string;
      requires_consent?: boolean;
    }>
  >([]);
  const [selectedPipelinePresetId, setSelectedPipelinePresetId] = useState<string>("");
  const [qualityLevel, setQualityLevel] = useState<"low" | "standard" | "pro">("standard");
  const [isLoadingPipelinePresets, setIsLoadingPipelinePresets] = useState(false);
  const [postProcessing, setPostProcessing] = useState<{
    face_restoration: boolean;
    upscale: boolean;
    film_grain: boolean;
    tone_mapping: boolean;
  }>({
    face_restoration: false,
    upscale: false,
    film_grain: false,
    tone_mapping: false,
  });

  async function loadPresets() {
    setIsLoadingPresets(true);
    try {
      const res = await apiGet<{ ok: boolean; items: typeof presets }>(
        "/api/generate/presets"
      );
      if (res.ok && Array.isArray(res.items)) {
        setPresets(res.items);
      }
    } catch (e) {
      // non-fatal
    } finally {
      setIsLoadingPresets(false);
    }
  }

  async function loadPipelinePresets() {
    setIsLoadingPipelinePresets(true);
    try {
      const res = await apiGet<{ ok: boolean; presets: typeof pipelinePresets }>(
        "/api/pipeline/presets"
      );
      if (res.ok && Array.isArray(res.presets)) {
        setPipelinePresets(res.presets);
      }
    } catch (e) {
      // non-fatal
    } finally {
      setIsLoadingPipelinePresets(false);
    }
  }

  function applyPreset(presetId: string) {
    const preset = presets.find((p) => p.id === presetId);
    if (!preset) return;

    setSelectedPresetId(presetId);

    if (preset.prompt_template) {
      const template = preset.prompt_template.replace(/{subject}/g, "");
      if (template.trim()) {
        setPrompt(template.trim());
      }
    }
    if (preset.negative_prompt) setNegative(preset.negative_prompt);
    if (preset.width) setWidth(String(preset.width));
    if (preset.height) setHeight(String(preset.height));
    if (preset.steps) setSteps(String(preset.steps));
    if (preset.cfg) setCfg(String(preset.cfg));
    if (preset.sampler_name) setSamplerName(preset.sampler_name);
    if (preset.scheduler) setScheduler(preset.scheduler);
    if (preset.batch_size) setBatchSize(String(preset.batch_size));
    if (preset.checkpoint && checkpoints.includes(preset.checkpoint)) {
      setCheckpoint(preset.checkpoint);
    }

    if (preset.post_processing) {
      setPostProcessing({
        face_restoration:
          preset.post_processing.face_restoration?.enabled ?? false,
        upscale: preset.post_processing.upscale?.enabled ?? false,
        film_grain: preset.post_processing.film_grain?.enabled ?? false,
        tone_mapping: preset.post_processing.tone_mapping?.enabled ?? false,
      });
    } else {
      setPostProcessing({
        face_restoration: false,
        upscale: false,
        film_grain: false,
        tone_mapping: false,
      });
    }
  }

  async function refreshComfy() {
    try {
      const settings = await apiGet<{
        comfyui_base_url: string;
        comfyui_base_url_source: string;
      }>("/api/settings");
      setComfyBaseUrlInput(settings.comfyui_base_url ?? "");
    } catch (e) {
      // non-fatal
    }

    try {
      const s = await apiGet<{
        ok: boolean;
        base_url: string;
        base_url_source?: string;
        error?: string;
      }>("/api/comfyui/status");
      setComfyStatus(s);
    } catch (e) {
      setComfyStatus({
        ok: false,
        base_url: "",
        error: "Unable to reach backend",
      });
    }

    try {
      const c = await apiGet<{ ok: boolean; checkpoints: string[] }>(
        "/api/comfyui/checkpoints"
      );
      const list = Array.isArray(c.checkpoints) ? c.checkpoints : [];
      setCheckpoints(list);
      if (!checkpoint && list.length) setCheckpoint(list[0]);
    } catch (e) {
      setCheckpoints([]);
    }

    try {
      const s = await apiGet<{ ok: boolean; samplers: string[] }>(
        "/api/comfyui/samplers"
      );
      const list = Array.isArray(s.samplers) ? s.samplers : [];
      setSamplers(list);
      if (list.length && !list.includes(samplerName)) setSamplerName(list[0]);
    } catch (e) {
      setSamplers([]);
    }

    try {
      const sc = await apiGet<{ ok: boolean; schedulers: string[] }>(
        "/api/comfyui/schedulers"
      );
      const list = Array.isArray(sc.schedulers) ? sc.schedulers : [];
      setSchedulers(list);
      if (list.length && !list.includes(scheduler)) setScheduler(list[0]);
    } catch (e) {
      setSchedulers([]);
    }
  }

  async function refreshGallery(reset: boolean = true) {
    try {
      if (reset) setIsLoadingGallery(true);
      const offset = reset ? 0 : galleryOffset;
      const params = new URLSearchParams({
        q: galleryQuery.trim(),
        sort: gallerySort,
        limit: String(galleryLimit),
        offset: String(offset),
      });
      const g = await apiGet<{
        items: ImageItem[];
        total: number;
        limit: number;
        offset: number;
      }>(`/api/content/images?${params.toString()}`);
      if (reset) {
        setGallery(g.items ?? []);
      } else {
        setGallery((prev) => [...prev, ...(g.items ?? [])]);
      }
      setGalleryTotal(g.total ?? 0);
      setGalleryOffset((g.offset ?? offset) + (g.limit ?? galleryLimit));
    } catch (e) {
      // non-fatal
    } finally {
      setIsLoadingGallery(false);
    }
  }

  async function deleteGalleryImage(path: string) {
    setIsDeletingImage(path);
    try {
      await fetch(
        `${API_BASE_URL}/api/content/images/${encodeURIComponent(path)}`,
        { method: "DELETE" }
      );
      await refreshGallery(true);
      await refreshStorage();
    } catch (e) {
      // non-fatal
    } finally {
      setIsDeletingImage(null);
    }
  }

  async function bulkDeleteSelectedImages() {
    const filenames = Object.keys(selectedImages).filter(
      (k) => selectedImages[k]
    );
    if (!filenames.length) return;
    setIsBulkDeletingImages(true);
    try {
      await apiPost("/api/content/images/delete", { filenames });
      setSelectedImages({});
      await refreshGallery(true);
      await refreshStorage();
    } catch (e) {
      // non-fatal
    } finally {
      setIsBulkDeletingImages(false);
    }
  }

  async function cleanupOlderThan() {
    setIsCleaningUp(true);
    try {
      const days = Number(cleanupDays);
      await apiPost("/api/content/images/cleanup", {
        older_than_days: Number.isFinite(days) ? days : 30,
      });
      setSelectedImages({});
      await refreshGallery(true);
      await refreshStorage();
    } catch (e) {
      // non-fatal
    } finally {
      setIsCleaningUp(false);
    }
  }

  async function refreshJob(jobId: string) {
    try {
      const res = await apiGet<{
        ok: boolean;
        job?: ImageJob;
        error?: string;
      }>(`/api/generate/image/${jobId}`);
      if (res.ok && res.job) {
        setJob(res.job);
        setSelectedJobId(res.job.id);
      }
    } catch (e) {
      // non-fatal
    }
  }

  async function refreshJobs() {
    try {
      const res = await apiGet<{ items: ImageJob[] }>(
        "/api/generate/image/jobs"
      );
      setJobs(res.items ?? []);
    } catch (e) {
      // non-fatal
    }
  }

  async function refreshStorage() {
    try {
      const s = await apiGet<{ images_count: number; images_bytes: number }>(
        "/api/generate/storage"
      );
      setStorage(s);
    } catch (e) {
      // non-fatal
    }
  }

  useEffect(() => {
    void loadPresets();
    void loadPipelinePresets();
    void refreshComfy();
    void refreshGallery(true);
    void refreshJobs();
    void refreshStorage();
    const t = window.setInterval(() => {
      void refreshComfy();
      void refreshJobs();
      void refreshStorage();
      if (job?.id) void refreshJob(job.id);
    }, 1500);
    return () => window.clearInterval(t);
  }, [job?.id]);

  async function saveComfyBaseUrl() {
    setIsSavingComfyUrl(true);
    try {
      await apiPut("/api/settings", { comfyui_base_url: comfyBaseUrlInput });
      await refreshComfy();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsSavingComfyUrl(false);
    }
  }

  useEffect(() => {
    setSelectedImages({});
    setGalleryOffset(0);
    void refreshGallery(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [galleryQuery, gallerySort]);

  const canSubmit = useMemo(
    () => prompt.trim().length > 0 && !isSubmitting,
    [prompt, isSubmitting]
  );

  function handlePresetChange(presetId: string) {
    setSelectedPresetId(presetId);
    if (presetId) {
      applyPreset(presetId);
    }
  }

  async function submit() {
    setIsSubmitting(true);
    try {
      setError(null);

      // Use pipeline API if pipeline preset is selected
      if (selectedPipelinePresetId) {
        const payload: Record<string, unknown> = {
          preset_id: selectedPipelinePresetId,
          prompt: prompt || "A beautiful image",
          quality_level: qualityLevel,
        };
        if (negative.trim()) payload.negative_prompt = negative;
        if (seed.trim()) payload.seed = Number(seed);

        try {
          const res = await apiPost<{
            job_id: string;
            status: string;
            preset_id: string;
            output_url?: string | null;
            error?: string | null;
          }>("/api/pipeline/generate/image", payload);

          // Convert pipeline response to ImageJob format for compatibility
          const pipelineJob: ImageJob = {
            id: res.job_id,
            state: res.status as ImageJob["state"],
            image_path: res.output_url || null,
            error: res.error || null,
          };
          setJob(pipelineJob);
          setSelectedJobId(res.job_id);
          setPrompt("");
          setNegative("");
          setSeed("");
          setSelectedPipelinePresetId(""); // Reset after submission
        } catch (e: unknown) {
          const err = e as { response?: { data?: { error_code?: string; message?: string; remediation?: string[] } } };
          if (err.response?.data?.error_code === "ENGINE_OFFLINE") {
            setError(
              `ComfyUI is not running. ${err.response.data.remediation?.join(" ") || "Please start ComfyUI in Setup."}`
            );
          } else {
            setError(
              err instanceof Error
                ? err.message
                : err.response?.data?.message || String(e)
            );
          }
        }
        return;
      }

      // Original API for non-pipeline presets
      const payload: Record<string, unknown> = { prompt };
      if (negative.trim()) payload.negative_prompt = negative;
      if (seed.trim()) payload.seed = Number(seed);
      if (checkpoint.trim()) payload.checkpoint = checkpoint.trim();
      if (width.trim()) payload.width = Number(width);
      if (height.trim()) payload.height = Number(height);
      if (steps.trim()) payload.steps = Number(steps);
      if (cfg.trim()) payload.cfg = Number(cfg);
      if (samplerName.trim()) payload.sampler_name = samplerName.trim();
      if (scheduler.trim()) payload.scheduler = scheduler.trim();
      if (batchSize.trim()) payload.batch_size = Number(batchSize);
      const res = await apiPost<{ ok: boolean; job: ImageJob }>(
        "/api/generate/image",
        payload
      );
      setJob(res.job);
      setSelectedJobId(res.job.id);
      setPrompt("");
      setNegative("");
      setSeed("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function cancelJob(jobId: string) {
    setIsCancelling(jobId);
    try {
      await apiPost<{ ok: boolean }>(`/api/generate/image/${jobId}/cancel`, {});
      await refreshJobs();
      if (job?.id === jobId) await refreshJob(jobId);
    } catch (e) {
      // non-fatal
    } finally {
      setIsCancelling(null);
    }
  }

  async function viewJob(jobId: string) {
    setSelectedJobId(jobId);
    await refreshJob(jobId);
  }

  async function deleteJob(jobId: string) {
    setIsDeleting(jobId);
    try {
      await fetch(`${API_BASE_URL}/api/generate/image/${jobId}`, {
        method: "DELETE",
      });
      if (selectedJobId === jobId) {
        setSelectedJobId(null);
        setJob(null);
      }
      await refreshJobs();
      await refreshGallery();
      await refreshStorage();
    } catch (e) {
      // non-fatal
    } finally {
      setIsDeleting(null);
    }
  }

  async function clearAll() {
    setIsClearing(true);
    try {
      await apiPost("/api/generate/clear", {});
      setSelectedJobId(null);
      setJob(null);
      await refreshJobs();
      await refreshGallery();
      await refreshStorage();
    } catch (e) {
      // non-fatal
    } finally {
      setIsClearing(false);
    }
  }

  function formatBytes(n: number) {
    const units = ["B", "KB", "MB", "GB", "TB"];
    let v = n;
    let i = 0;
    while (v >= 1024 && i < units.length - 1) {
      v /= 1024;
      i += 1;
    }
    return `${v.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
  }

  const hasMoreGallery = useMemo(
    () => gallery.length < galleryTotal,
    [gallery.length, galleryTotal]
  );

  const selectedCount = useMemo(
    () => Object.values(selectedImages).filter(Boolean).length,
    [selectedImages]
  );

  const getJobStatusChip = (state: string) => {
    switch (state) {
      case "succeeded":
        return "success";
      case "failed":
        return "error";
      case "running":
      case "queued":
        return "info";
      case "cancelled":
        return "warning";
      default:
        return "info";
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        <PageHeader
          title="Generate"
          description="Create images with ComfyUI. Send a prompt, save the output image locally, and view it in the gallery."
          action={
            <div className="flex gap-2">
              <Link href="/">
                <SecondaryButton size="sm" icon={<Home className="h-4 w-4" />}>
                  Home
                </SecondaryButton>
              </Link>
              <Link href="/models">
                <SecondaryButton
                  size="sm"
                  icon={<Package className="h-4 w-4" />}
                >
                  Models
                </SecondaryButton>
              </Link>
            </div>
          }
        />

        {error && (
          <div className="mb-6">
            <ErrorBanner
              title="Error"
              message={error}
              remediation={
                error.includes("ComfyUI is not running") || error.includes("ENGINE_OFFLINE") ? (
                  <div className="space-y-2">
                    <p className="text-sm">ComfyUI is not running. Please start it to generate images.</p>
                    <Link href="/comfyui">
                      <PrimaryButton size="sm">Go to Setup → Start ComfyUI</PrimaryButton>
                    </Link>
                  </div>
                ) : {
                  label: "Dismiss",
                  onClick: () => setError(null),
                }
              }
            />
          </div>
        )}

        {/* ComfyUI Status */}
        {!comfyStatus?.ok && (
          <div className="mb-6">
            <Alert
              title={
                comfyStatus?.action_required === "install"
                  ? "ComfyUI Not Installed"
                  : comfyStatus?.action_required === "start"
                  ? "ComfyUI Not Running"
                  : comfyStatus?.action_required === "wait"
                  ? "ComfyUI Starting..."
                  : "ComfyUI Not Available"
              }
              message={
                comfyStatus?.message ||
                comfyStatus?.error ||
                "ComfyUI is not reachable."
              }
              variant={
                comfyStatus?.action_required === "wait" ? "info" : "warning"
              }
              action={
                comfyStatus?.action_required === "install"
                  ? {
                      label: "Install ComfyUI",
                      onClick: async () => {
                        try {
                          await apiPost("/api/comfyui/manager/install");
                          alert(
                            "ComfyUI installation started. This may take a few minutes. Check the status again in a moment."
                          );
                          await refreshComfy();
                        } catch (e) {
                          alert(
                            `Failed to install ComfyUI: ${
                              e instanceof Error ? e.message : String(e)
                            }`
                          );
                        }
                      },
                    }
                  : comfyStatus?.action_required === "start"
                  ? {
                      label: "Start ComfyUI",
                      onClick: async () => {
                        try {
                          await apiPost("/api/comfyui/manager/start");
                          alert(
                            "ComfyUI is starting. Please wait a moment and refresh."
                          );
                          setTimeout(() => refreshComfy(), 2000);
                        } catch (e) {
                          alert(
                            `Failed to start ComfyUI: ${
                              e instanceof Error ? e.message : String(e)
                            }`
                          );
                        }
                      },
                    }
                  : undefined
              }
            />
          </div>
        )}

        {comfyStatus?.ok && checkpoints.length === 0 && (
          <div className="mb-6">
            <Alert
              title="No Checkpoints Found"
              message="ComfyUI is running but no checkpoints were found. Install at least one checkpoint in ComfyUI's models/checkpoints folder, then refresh."
              variant="warning"
            />
          </div>
        )}

        {/* ComfyUI Status Card */}
        <SectionCard
          title="ComfyUI Status"
          description={
            comfyStatus ? (
              comfyStatus.ok ? (
                <span>
                  Connected to{" "}
                  <code className="rounded bg-[var(--bg-surface)] px-1 py-0.5 text-xs">
                    {comfyStatus.base_url}
                  </code>
                </span>
              ) : (
                <span className="text-[var(--error)]">
                  Not reachable {comfyStatus.error && `— ${comfyStatus.error}`}
                </span>
              )
            ) : (
              "Checking…"
            )
          }
          action={
            <IconButton
              icon={<RefreshCw className="h-4 w-4" />}
              size="sm"
              variant="ghost"
              onClick={() => void refreshComfy()}
              aria-label="Refresh ComfyUI status"
            />
          }
          className="mb-6"
        >
          <div className="space-y-4">
            <div className="text-xs text-[var(--text-muted)]">
              Source:{" "}
              <span className="font-medium">
                {comfyStatus?.base_url_source ?? "—"}
              </span>
              . Env override:{" "}
              <code className="rounded bg-[var(--bg-surface)] px-1 py-0.5">
                AINFLUENCER_COMFYUI_BASE_URL
              </code>
              .
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Input
                value={comfyBaseUrlInput}
                onChange={(e) => setComfyBaseUrlInput(e.target.value)}
                placeholder="http://localhost:8188"
                className="max-w-[360px]"
              />
              <SecondaryButton
                onClick={() => void saveComfyBaseUrl()}
                disabled={isSavingComfyUrl}
                loading={isSavingComfyUrl}
                size="sm"
              >
                Save URL
              </SecondaryButton>
            </div>
          </div>
        </SectionCard>

        {/* Storage Card */}
        <SectionCard
          title="Storage"
          description={
            storage
              ? `${storage.images_count} images • ${formatBytes(
                  storage.images_bytes
                )}`
              : "—"
          }
          action={
            <SecondaryButton
              size="sm"
              onClick={() => void clearAll()}
              disabled={isClearing}
              loading={isClearing}
            >
              Clear All
            </SecondaryButton>
          }
          className="mb-6"
        >
          <div className="space-y-4">
            <div className="text-xs text-[var(--text-muted)]">
              This is `.ainfluencer/content/images` on disk.
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Input
                value={cleanupDays}
                onChange={(e) => setCleanupDays(e.target.value)}
                placeholder="days"
                type="number"
                className="w-[110px]"
              />
              <SecondaryButton
                onClick={() => void cleanupOlderThan()}
                disabled={isCleaningUp}
                loading={isCleaningUp}
                size="sm"
              >
                Delete older than (days)
              </SecondaryButton>
            </div>
          </div>
        </SectionCard>

        {/* Generation Form */}
        <SectionCard title="Generate Image" className="mb-6">
          <FormGroup>
            <Select
              label="Pipeline Preset (New - Recommended)"
              options={[
                { value: "", label: "None (use custom settings below)" },
                ...pipelinePresets.map((p) => ({
                  value: p.id,
                  label: `${p.name} - ${p.description}${p.requires_consent ? " (requires consent)" : ""}`,
                })),
              ]}
              value={selectedPipelinePresetId}
              onChange={(e) => {
                setSelectedPipelinePresetId(e.target.value);
                if (e.target.value) {
                  setSelectedPresetId(""); // Clear old preset
                }
              }}
              disabled={isLoadingPipelinePresets}
            />
            {selectedPipelinePresetId && (
              <div className="mt-2 space-y-2">
                <Select
                  label="Quality Level"
                  options={[
                    { value: "low", label: "Low (faster)" },
                    { value: "standard", label: "Standard (balanced)" },
                    { value: "pro", label: "Pro (best quality)" },
                  ]}
                  value={qualityLevel}
                  onChange={(e) => setQualityLevel(e.target.value as "low" | "standard" | "pro")}
                />
                <div className="text-xs text-[var(--text-secondary)] bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/20 rounded p-2">
                  ✓ Using new Pipeline API. Settings below are ignored when using pipeline presets.
                </div>
              </div>
            )}
            <Select
              label="Legacy Workflow Preset (optional)"
              options={[
                { value: "", label: "Custom (no preset)" },
                ...presets
                  .filter((p) => p.category === "quality")
                  .map((p) => ({
                    value: p.id,
                    label: `⭐ ${p.name} - ${p.description}`,
                  })),
                ...presets
                  .filter((p) => p.category !== "quality")
                  .map((p) => ({
                    value: p.id,
                    label: `${p.name} - ${p.description}`,
                  })),
              ]}
              value={selectedPresetId}
              onChange={(e) => {
                handlePresetChange(e.target.value);
                if (e.target.value) {
                  setSelectedPipelinePresetId(""); // Clear pipeline preset
                }
              }}
              disabled={isLoadingPresets || !!selectedPipelinePresetId}
            />
            {selectedPresetId && (
              <div className="space-y-2">
                <div className="text-xs text-[var(--text-secondary)]">
                  Preset applied:{" "}
                  {presets.find((p) => p.id === selectedPresetId)?.name}. You
                  can still modify any settings below.
                </div>
                {(() => {
                  const preset = presets.find((p) => p.id === selectedPresetId);
                  if (!preset?.post_processing) return null;

                  const isQualityPreset = preset.category === "quality";
                  if (!isQualityPreset) return null;

                  return (
                    <div className="rounded-lg border border-[var(--accent-primary)]/20 bg-[var(--accent-primary)]/5 p-3">
                      <div className="text-xs font-medium text-[var(--accent-primary)] mb-2">
                        Post-Processing Options
                      </div>
                      <div className="space-y-2">
                        {preset.post_processing.face_restoration && (
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={postProcessing.face_restoration}
                              onChange={(e) =>
                                setPostProcessing({
                                  ...postProcessing,
                                  face_restoration: e.target.checked,
                                })
                              }
                              className="w-4 h-4 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
                            />
                            <span className="text-xs text-[var(--text-primary)]">
                              Face Restoration (GFPGAN/CodeFormer) - Enhances
                              facial details and skin quality
                            </span>
                          </label>
                        )}
                        {preset.post_processing.upscale && (
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={postProcessing.upscale}
                              onChange={(e) =>
                                setPostProcessing({
                                  ...postProcessing,
                                  upscale: e.target.checked,
                                })
                              }
                              className="w-4 h-4 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
                            />
                            <span className="text-xs text-[var(--text-primary)]">
                              Upscale (Real-ESRGAN) - Increases image resolution
                            </span>
                          </label>
                        )}
                        {preset.post_processing.film_grain && (
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={postProcessing.film_grain}
                              onChange={(e) =>
                                setPostProcessing({
                                  ...postProcessing,
                                  film_grain: e.target.checked,
                                })
                              }
                              className="w-4 h-4 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
                            />
                            <span className="text-xs text-[var(--text-primary)]">
                              Film Grain - Adds cinematic film texture
                            </span>
                          </label>
                        )}
                        {preset.post_processing.tone_mapping && (
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={postProcessing.tone_mapping}
                              onChange={(e) =>
                                setPostProcessing({
                                  ...postProcessing,
                                  tone_mapping: e.target.checked,
                                })
                              }
                              className="w-4 h-4 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
                            />
                            <span className="text-xs text-[var(--text-primary)]">
                              Tone Mapping - Applies cinematic color grading
                            </span>
                          </label>
                        )}
                      </div>
                      {preset.optimization_notes && (
                        <div className="mt-2 text-xs text-[var(--text-secondary)] italic">
                          💡 {preset.optimization_notes}
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>
            )}

            <Textarea
              label="Prompt"
              required
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="A cinematic portrait photo of…"
              rows={4}
            />

            <Input
              label="Negative prompt (optional)"
              value={negative}
              onChange={(e) => setNegative(e.target.value)}
              placeholder="blurry, low quality, artifacts…"
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <Select
                label="Checkpoint"
                options={[
                  ...(checkpoints.length
                    ? checkpoints.map((c) => ({ value: c, label: c }))
                    : [{ value: "", label: "(no checkpoints found)" }]),
                ]}
                value={checkpoint}
                onChange={(e) => setCheckpoint(e.target.value)}
                disabled={!checkpoints.length}
              />
              <div className="text-xs text-[var(--text-muted)] sm:flex sm:items-end">
                ComfyUI must have at least one checkpoint installed.
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Input
                label="Seed (optional)"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                placeholder="0"
                type="number"
              />
              <div className="flex items-end">
                <PrimaryButton
                  onClick={() => void submit()}
                  disabled={!canSubmit}
                  loading={isSubmitting}
                  icon={<Sparkles className="h-4 w-4" />}
                  className="w-full"
                >
                  Generate
                </PrimaryButton>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <Input
                label="Width"
                value={width}
                onChange={(e) => setWidth(e.target.value)}
                type="number"
              />
              <Input
                label="Height"
                value={height}
                onChange={(e) => setHeight(e.target.value)}
                type="number"
              />
              <Input
                label="Batch"
                value={batchSize}
                onChange={(e) => setBatchSize(e.target.value)}
                type="number"
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-4">
              <Input
                label="Steps"
                value={steps}
                onChange={(e) => setSteps(e.target.value)}
                type="number"
              />
              <Input
                label="CFG"
                value={cfg}
                onChange={(e) => setCfg(e.target.value)}
                type="number"
                step="0.1"
              />
              <Select
                label="Sampler"
                options={[
                  ...(samplers.length
                    ? samplers.map((s) => ({ value: s, label: s }))
                    : [{ value: "euler", label: "euler" }]),
                ]}
                value={samplerName}
                onChange={(e) => setSamplerName(e.target.value)}
                disabled={!samplers.length}
              />
              <Select
                label="Scheduler"
                options={[
                  ...(schedulers.length
                    ? schedulers.map((s) => ({ value: s, label: s }))
                    : [{ value: "normal", label: "normal" }]),
                ]}
                value={scheduler}
                onChange={(e) => setScheduler(e.target.value)}
                disabled={!schedulers.length}
              />
            </div>

            <div className="text-xs text-[var(--text-muted)]">
              Requires ComfyUI running at{" "}
              <code className="rounded bg-[var(--bg-surface)] px-1 py-0.5">
                {API_BASE_URL}
              </code>{" "}
              + ComfyUI at{" "}
              <code className="rounded bg-[var(--bg-surface)] px-1 py-0.5">
                AINFLUENCER_COMFYUI_BASE_URL
              </code>{" "}
              (default http://localhost:8188).
            </div>
          </FormGroup>
        </SectionCard>

        {/* Job History */}
        <SectionCard
          title="Job History"
          action={
            <IconButton
              icon={<RefreshCw className="h-4 w-4" />}
              size="sm"
              variant="ghost"
              onClick={() => void refreshJobs()}
              aria-label="Refresh jobs"
            />
          }
          className="mb-6"
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-[var(--text-secondary)] border-b border-[var(--border-base)]">
                <tr>
                  <th className="py-2">State</th>
                  <th className="py-2">Checkpoint</th>
                  <th className="py-2">WxH</th>
                  <th className="py-2">Steps/CFG</th>
                  <th className="py-2">Created</th>
                  <th className="py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr
                    key={j.id}
                    className={`border-t border-[var(--border-base)] ${
                      selectedJobId === j.id
                        ? "bg-[var(--bg-surface)]"
                        : "hover:bg-[var(--bg-surface)]"
                    } transition-colors`}
                  >
                    <td className="py-2">
                      <StatusChip
                        status={getJobStatusChip(j.state)}
                        label={j.state}
                      />
                    </td>
                    <td className="py-2 text-xs text-[var(--text-primary)]">
                      {String(j.params?.checkpoint ?? "-")}
                    </td>
                    <td className="py-2 text-xs text-[var(--text-primary)]">
                      {String(j.params?.width ?? "-")}x
                      {String(j.params?.height ?? "-")}
                    </td>
                    <td className="py-2 text-xs text-[var(--text-primary)]">
                      {String(j.params?.steps ?? "-")} /{" "}
                      {String(j.params?.cfg ?? "-")}
                    </td>
                    <td className="py-2 text-xs text-[var(--text-muted)]">
                      {j.created_at
                        ? new Date(j.created_at * 1000).toLocaleString()
                        : "-"}
                    </td>
                    <td className="py-2 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <SecondaryButton
                          size="sm"
                          onClick={() => void viewJob(j.id)}
                        >
                          View
                        </SecondaryButton>
                        <a
                          href={`${API_BASE_URL}/api/generate/image/${j.id}/download`}
                          download
                        >
                          <SecondaryButton
                            size="sm"
                            icon={<Download className="h-3 w-3" />}
                          >
                            ZIP
                          </SecondaryButton>
                        </a>
                        <IconButton
                          icon={<Trash2 className="h-4 w-4" />}
                          size="sm"
                          variant="ghost"
                          onClick={() => void deleteJob(j.id)}
                          disabled={isDeleting === j.id}
                          aria-label="Delete job"
                          className="text-[var(--error)] hover:bg-[var(--error-bg)]"
                        />
                        {(j.state === "running" || j.state === "queued") && (
                          <SecondaryButton
                            size="sm"
                            onClick={() => void cancelJob(j.id)}
                            disabled={isCancelling === j.id}
                            loading={isCancelling === j.id}
                          >
                            Cancel
                          </SecondaryButton>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {!jobs.length && (
                  <tr>
                    <td
                      className="py-3 text-[var(--text-muted)] text-center"
                      colSpan={6}
                    >
                      (no jobs yet)
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </SectionCard>

        {/* Latest Job */}
        {job && (
          <SectionCard
            title="Latest Job"
            action={
              <a
                href={`${API_BASE_URL}/api/generate/image/${job.id}/download`}
                download
              >
                <SecondaryButton
                  size="sm"
                  icon={<Download className="h-4 w-4" />}
                >
                  Download ZIP
                </SecondaryButton>
              </a>
            }
            className="mb-6"
          >
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <StatusChip
                  status={getJobStatusChip(job.state)}
                  label={job.state}
                />
                <span className="text-sm text-[var(--text-secondary)]">
                  {job.message ?? "-"}
                </span>
              </div>
              {job.error && <Alert message={job.error} variant="error" />}
              {job.state === "running" && (
                <ProgressIndicator
                  variant="linear"
                  value={50}
                  label="Generating..."
                />
              )}
              {job.image_paths && job.image_paths.length > 0 && (
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {job.image_paths.map((p) => (
                    <a
                      key={p}
                      href={`${API_BASE_URL}/content/images/${p}`}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-lg border border-[var(--border-base)] overflow-hidden hover:border-[var(--accent-primary)] transition-colors"
                    >
                      <img
                        src={`${API_BASE_URL}/content/images/${p}`}
                        alt="generated"
                        className="aspect-square w-full object-cover"
                      />
                    </a>
                  ))}
                </div>
              )}
              {job.image_path && !job.image_paths && (
                <div>
                  <img
                    src={`${API_BASE_URL}/content/images/${job.image_path}`}
                    alt="generated"
                    className="max-h-[380px] rounded-lg border border-[var(--border-base)] object-contain"
                  />
                </div>
              )}
            </div>
          </SectionCard>
        )}

        {/* Gallery */}
        <SectionCard
          title="Gallery"
          description={`Showing ${gallery.length} of ${galleryTotal} images`}
          action={
            <div className="flex items-center gap-2">
              <a href={`${API_BASE_URL}/api/content/images/download`} download>
                <SecondaryButton
                  size="sm"
                  icon={<Download className="h-4 w-4" />}
                >
                  Download ZIP
                </SecondaryButton>
              </a>
              <IconButton
                icon={<RefreshCw className="h-4 w-4" />}
                size="sm"
                variant="ghost"
                onClick={() => void refreshGallery(true)}
                aria-label="Refresh gallery"
              />
            </div>
          }
          loading={isLoadingGallery && gallery.length === 0}
          empty={!isLoadingGallery && gallery.length === 0}
          emptyMessage="No images in gallery yet"
        >
          <div className="space-y-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-1 items-center gap-2">
                <Input
                  value={galleryQuery}
                  onChange={(e) => setGalleryQuery(e.target.value)}
                  placeholder="Search filenames…"
                  className="flex-1"
                />
                <Select
                  options={[
                    { value: "newest", label: "Newest" },
                    { value: "oldest", label: "Oldest" },
                    { value: "name", label: "Name" },
                  ]}
                  value={gallerySort}
                  onChange={(e) =>
                    setGallerySort(
                      e.target.value as "newest" | "oldest" | "name"
                    )
                  }
                  className="w-[140px]"
                />
              </div>

              <div className="flex items-center gap-2">
                <SecondaryButton
                  size="sm"
                  onClick={() => {
                    const next: Record<string, boolean> = {};
                    for (const it of gallery) next[it.path] = true;
                    setSelectedImages(next);
                  }}
                >
                  Select All
                </SecondaryButton>
                <SecondaryButton
                  size="sm"
                  onClick={() => setSelectedImages({})}
                >
                  Clear
                </SecondaryButton>
                <PrimaryButton
                  size="sm"
                  onClick={() => void bulkDeleteSelectedImages()}
                  disabled={!selectedCount || isBulkDeletingImages}
                  loading={isBulkDeletingImages}
                  icon={<Trash2 className="h-4 w-4" />}
                >
                  Delete ({selectedCount})
                </PrimaryButton>
              </div>
            </div>

            {gallery.length > 0 && (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                {gallery.map((img) => (
                  <div
                    key={img.path}
                    className="group overflow-hidden rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] hover:border-[var(--accent-primary)] transition-all"
                  >
                    <a
                      href={`${API_BASE_URL}${img.url}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <img
                        src={`${API_BASE_URL}${img.url}`}
                        alt={img.path}
                        className="aspect-square w-full object-cover"
                      />
                    </a>
                    <div className="flex items-center justify-between gap-2 border-t border-[var(--border-base)] px-2 py-2">
                      <div
                        className="truncate text-[11px] text-[var(--text-secondary)]"
                        title={img.path}
                      >
                        {img.path}
                      </div>
                      <div className="flex items-center gap-2">
                        <label className="flex items-center gap-1 text-[11px] text-[var(--text-secondary)] cursor-pointer">
                          <input
                            type="checkbox"
                            checked={!!selectedImages[img.path]}
                            onChange={(e) => {
                              const checked = e.target.checked;
                              setSelectedImages((prev) => ({
                                ...prev,
                                [img.path]: checked,
                              }));
                            }}
                            className="w-3 h-3 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
                          />
                          Select
                        </label>
                        <IconButton
                          icon={<Trash2 className="h-3 w-3" />}
                          size="sm"
                          variant="ghost"
                          onClick={() => void deleteGalleryImage(img.path)}
                          disabled={isDeletingImage === img.path}
                          aria-label="Delete image"
                          className="text-[var(--error)] hover:bg-[var(--error-bg)]"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {hasMoreGallery && (
              <div className="flex justify-center">
                <SecondaryButton
                  onClick={() => void refreshGallery(false)}
                  disabled={isLoadingGallery}
                  loading={isLoadingGallery}
                >
                  Load More
                </SecondaryButton>
              </div>
            )}
          </div>
        </SectionCard>
      </main>
    </div>
  );
}
