"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { API_BASE_URL, apiGet, apiPost } from "@/lib/api";

type ImageJob = {
  id: string;
  state: "queued" | "running" | "failed" | "succeeded";
  message?: string | null;
  created_at?: number;
  started_at?: number | null;
  finished_at?: number | null;
  image_path?: string | null;
  error?: string | null;
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
  const [comfyStatus, setComfyStatus] = useState<{ ok: boolean; base_url: string; error?: string } | null>(null);
  const [checkpoints, setCheckpoints] = useState<string[]>([]);
  const [job, setJob] = useState<ImageJob | null>(null);
  const [gallery, setGallery] = useState<ImageItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  useEffect(() => {
    void refreshComfy();
    void refreshGallery();
    const t = window.setInterval(() => {
      void refreshComfy();
      void refreshGallery();
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

            <div className="mt-2 text-xs text-zinc-500">
              Requires ComfyUI running at <code className="rounded bg-zinc-100 px-1 py-0.5">{API_BASE_URL}</code> +
              ComfyUI at <code className="rounded bg-zinc-100 px-1 py-0.5">AINFLUENCER_COMFYUI_BASE_URL</code> (default
              http://localhost:8188).
            </div>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="text-sm font-semibold">Latest job</div>
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
                {job.image_path ? (
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
