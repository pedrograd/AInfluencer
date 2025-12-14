"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { API_BASE_URL, apiGet, apiPost } from "@/lib/api";

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
  params?: Record<string, any> | null;
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
  const [comfyStatus, setComfyStatus] = useState<{ ok: boolean; base_url: string; error?: string } | null>(null);
  const [checkpoints, setCheckpoints] = useState<string[]>([]);
  const [job, setJob] = useState<ImageJob | null>(null);
  const [jobs, setJobs] = useState<ImageJob[]>([]);
  const [gallery, setGallery] = useState<ImageItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCancelling, setIsCancelling] = useState<string | null>(null);

  async function refreshComfy() {
    try {
      const s = await apiGet<{ ok: boolean; base_url: string; error?: string }>("/api/comfyui/status");
      setComfyStatus(s);
    } catch (e) {
      setComfyStatus({ ok: false, base_url: "", error: "Unable to reach backend" });
    }

    try {
      const c = await apiGet<{ ok: boolean; checkpoints: string[] }>("/api/comfyui/checkpoints");
      const list = Array.isArray(c.checkpoints) ? c.checkpoints : [];
      setCheckpoints(list);
      if (!checkpoint && list.length) setCheckpoint(list[0]);
    } catch (e) {
      setCheckpoints([]);
    }

    try {
      const s = await apiGet<{ ok: boolean; samplers: string[] }>("/api/comfyui/samplers");
      const list = Array.isArray(s.samplers) ? s.samplers : [];
      setSamplers(list);
      if (list.length && !list.includes(samplerName)) setSamplerName(list[0]);
    } catch (e) {
      setSamplers([]);
    }

    try {
      const sc = await apiGet<{ ok: boolean; schedulers: string[] }>("/api/comfyui/schedulers");
      const list = Array.isArray(sc.schedulers) ? sc.schedulers : [];
      setSchedulers(list);
      if (list.length && !list.includes(scheduler)) setScheduler(list[0]);
    } catch (e) {
      setSchedulers([]);
    }
  }

  async function refreshGallery() {
    try {
      const g = await apiGet<{ items: ImageItem[] }>("/api/content/images");
      setGallery(g.items);
    } catch (e) {
      // non-fatal
    }
  }

  async function refreshJob(jobId: string) {
    try {
      const res = await apiGet<{ ok: boolean; job?: ImageJob; error?: string }>(`/api/generate/image/${jobId}`);
      if (res.ok && res.job) setJob(res.job);
    } catch (e) {
      // non-fatal
    }
  }

  async function refreshJobs() {
    try {
      const res = await apiGet<{ items: ImageJob[] }>("/api/generate/image/jobs");
      setJobs(res.items ?? []);
    } catch (e) {
      // non-fatal
    }
  }

  useEffect(() => {
    void refreshComfy();
    void refreshGallery();
    void refreshJobs();
    const t = window.setInterval(() => {
      void refreshComfy();
      void refreshGallery();
      void refreshJobs();
      if (job?.id) void refreshJob(job.id);
    }, 1500);
    return () => window.clearInterval(t);
  }, [job?.id]);

  const canSubmit = useMemo(() => prompt.trim().length > 0 && !isSubmitting, [prompt, isSubmitting]);

  async function submit() {
    setIsSubmitting(true);
    try {
      setError(null);
      const payload: any = { prompt };
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
      const res = await apiPost<{ ok: boolean; job: ImageJob }>("/api/generate/image", payload);
      setJob(res.job);
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

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <div className="mx-auto w-full max-w-5xl px-6 py-10">
        <div className="flex items-start justify-between gap-6">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Generate</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
              MVP: send a prompt to ComfyUI, save the first output image locally, show it in the gallery.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Home
            </Link>
            <Link
              href="/models"
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Models
            </Link>
          </div>
        </div>

        {error ? (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        ) : null}

        {!comfyStatus?.ok ? (
          <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-5">
            <div className="text-sm font-semibold text-amber-900">Fix it</div>
            <div className="mt-2 text-sm text-amber-900/90">
              ComfyUI is not reachable. Start ComfyUI (default <code className="rounded bg-amber-100 px-1 py-0.5">http://localhost:8188</code>)
              or set <code className="rounded bg-amber-100 px-1 py-0.5">AINFLUENCER_COMFYUI_BASE_URL</code>.
            </div>
          </div>
        ) : checkpoints.length === 0 ? (
          <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-5">
            <div className="text-sm font-semibold text-amber-900">Fix it</div>
            <div className="mt-2 text-sm text-amber-900/90">
              ComfyUI is running but no checkpoints were found. Install at least one checkpoint in ComfyUI’s
              <code className="ml-1 rounded bg-amber-100 px-1 py-0.5">models/checkpoints</code> folder, then refresh.
            </div>
          </div>
        ) : null}

        <div className="mt-6 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-sm font-semibold">ComfyUI status</div>
              <div className="mt-1 text-sm text-zinc-700">
                {comfyStatus ? (
                  comfyStatus.ok ? (
                    <span>
                      Connected to <code className="rounded bg-zinc-100 px-1 py-0.5">{comfyStatus.base_url}</code>
                    </span>
                  ) : (
                    <span className="text-red-700">
                      Not reachable{" "}
                      {comfyStatus.error ? (
                        <span className="text-red-700">— {comfyStatus.error}</span>
                      ) : null}
                    </span>
                  )
                ) : (
                  "Checking…"
                )}
              </div>
              <div className="mt-2 text-xs text-zinc-500">
                Configure with{" "}
                <code className="rounded bg-zinc-100 px-1 py-0.5">AINFLUENCER_COMFYUI_BASE_URL</code> (default
                http://localhost:8188).
              </div>
            </div>
            <button
              type="button"
              onClick={() => void refreshComfy()}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="grid gap-3">
            <label className="text-xs font-medium text-zinc-600">Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="min-h-[90px] w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
              placeholder="A cinematic portrait photo of…"
            />

            <label className="text-xs font-medium text-zinc-600">Negative prompt (optional)</label>
            <input
              value={negative}
              onChange={(e) => setNegative(e.target.value)}
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
              placeholder="blurry, low quality, artifacts…"
            />

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="text-xs font-medium text-zinc-600">Checkpoint</label>
                <select
                  value={checkpoint}
                  onChange={(e) => setCheckpoint(e.target.value)}
                  className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                  disabled={!checkpoints.length}
                >
                  {checkpoints.length ? null : <option value="">(no checkpoints found)</option>}
                  {checkpoints.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div className="text-xs text-zinc-500 sm:flex sm:items-end">
                ComfyUI must have at least one checkpoint installed.
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="text-xs font-medium text-zinc-600">Seed (optional)</label>
                <input
                  value={seed}
                  onChange={(e) => setSeed(e.target.value)}
                  className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                  placeholder="0"
                  inputMode="numeric"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="button"
                  disabled={!canSubmit}
                  onClick={() => void submit()}
                  className="w-full rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isSubmitting ? "Starting…" : "Generate"}
                </button>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <label className="text-xs font-medium text-zinc-600">Width</label>
                <input
                  value={width}
                  onChange={(e) => setWidth(e.target.value)}
                  className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                  inputMode="numeric"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-zinc-600">Height</label>
                <input
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                  className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                  inputMode="numeric"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-zinc-600">Batch</label>
                <input
                  value={batchSize}
                  onChange={(e) => setBatchSize(e.target.value)}
                  className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                  inputMode="numeric"
                />
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-4">
              <div>
                <label className="text-xs font-medium text-zinc-600">Steps</label>
                <input
                  value={steps}
                  onChange={(e) => setSteps(e.target.value)}
                  className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                  inputMode="numeric"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-zinc-600">CFG</label>
                <input
                  value={cfg}
                  onChange={(e) => setCfg(e.target.value)}
                  className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                  inputMode="decimal"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-zinc-600">Sampler</label>
                <select
                  value={samplerName}
                  onChange={(e) => setSamplerName(e.target.value)}
                  className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                  disabled={!samplers.length}
                >
                  {samplers.length ? null : <option value="euler">euler</option>}
                  {samplers.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-zinc-600">Scheduler</label>
                <select
                  value={scheduler}
                  onChange={(e) => setScheduler(e.target.value)}
                  className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                  disabled={!schedulers.length}
                >
                  {schedulers.length ? null : <option value="normal">normal</option>}
                  {schedulers.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-2 text-xs text-zinc-500">
              Requires ComfyUI running at <code className="rounded bg-zinc-100 px-1 py-0.5">{API_BASE_URL}</code> +
              ComfyUI at <code className="rounded bg-zinc-100 px-1 py-0.5">AINFLUENCER_COMFYUI_BASE_URL</code> (default
              http://localhost:8188).
            </div>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold">Job history</div>
            <button
              type="button"
              onClick={() => void refreshJobs()}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Refresh
            </button>
          </div>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-zinc-500">
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
                  <tr key={j.id} className="border-t border-zinc-100">
                    <td className="py-2">{j.state}</td>
                    <td className="py-2 text-xs text-zinc-700">{String(j.params?.checkpoint ?? "-")}</td>
                    <td className="py-2 text-xs text-zinc-700">
                      {String(j.params?.width ?? "-")}x{String(j.params?.height ?? "-")}
                    </td>
                    <td className="py-2 text-xs text-zinc-700">
                      {String(j.params?.steps ?? "-")} / {String(j.params?.cfg ?? "-")}
                    </td>
                    <td className="py-2 text-xs text-zinc-700">
                      {j.created_at ? new Date(j.created_at * 1000).toLocaleString() : "-"}
                    </td>
                    <td className="py-2 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <a
                          href={`${API_BASE_URL}/api/generate/image/${j.id}/download`}
                          className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs font-medium hover:bg-zinc-50"
                        >
                          Download ZIP
                        </a>
                        {j.state === "running" || j.state === "queued" ? (
                          <button
                            type="button"
                            onClick={() => void cancelJob(j.id)}
                            disabled={isCancelling === j.id}
                            className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs font-medium hover:bg-zinc-50 disabled:opacity-50"
                          >
                            {isCancelling === j.id ? "Cancelling…" : "Cancel"}
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
                {!jobs.length ? (
                  <tr>
                    <td className="py-3 text-zinc-500" colSpan={6}>
                      (no jobs yet)
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="flex items-center justify-between gap-4">
            <div className="text-sm font-semibold">Latest job</div>
            {job ? (
              <a
                href={`${API_BASE_URL}/api/generate/image/${job.id}/download`}
                className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
              >
                Download ZIP
              </a>
            ) : null}
          </div>
          <div className="mt-2 text-sm text-zinc-700">
            {job ? (
              <div className="space-y-1">
                <div>
                  <span className="font-medium">State:</span> {job.state}
                </div>
                <div>
                  <span className="font-medium">Message:</span> {job.message ?? "-"}
                </div>
                {job.error ? (
                  <div className="text-sm text-red-700">
                    <span className="font-medium">Error:</span> {job.error}
                  </div>
                ) : null}
                {job.image_paths && job.image_paths.length ? (
                  <div className="pt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
                    {job.image_paths.map((p) => (
                      <a key={p} href={`${API_BASE_URL}/content/images/${p}`} target="_blank" rel="noreferrer">
                        <img
                          src={`${API_BASE_URL}/content/images/${p}`}
                          alt="generated"
                          className="aspect-square w-full rounded-lg border border-zinc-200 object-cover"
                        />
                      </a>
                    ))}
                  </div>
                ) : job.image_path ? (
                  <div className="pt-3">
                    <img
                      src={`${API_BASE_URL}/content/images/${job.image_path}`}
                      alt="generated"
                      className="max-h-[380px] rounded-lg border border-zinc-200 object-contain"
                    />
                  </div>
                ) : null}
              </div>
            ) : (
              "(none yet)"
            )}
          </div>
        </div>

        <div className="mt-8">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold">Gallery</div>
            <button
              type="button"
              onClick={() => void refreshGallery()}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Refresh
            </button>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {gallery.map((img) => (
              <a
                key={img.path}
                href={`${API_BASE_URL}${img.url}`}
                target="_blank"
                rel="noreferrer"
                className="group overflow-hidden rounded-lg border border-zinc-200 bg-white"
              >
                <img src={`${API_BASE_URL}${img.url}`} alt={img.path} className="aspect-square w-full object-cover" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
