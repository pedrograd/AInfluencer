"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { apiGet, apiPost } from "@/lib/api";

type CatalogItem = {
  id: string;
  name: string;
  type: string;
  url: string;
  filename: string;
  size_mb?: number | null;
  sha256?: string | null;
  notes?: string | null;
};

type InstalledItem = {
  path: string;
  size_bytes: number;
  mtime: number;
};

type DownloadStatus = {
  state: "idle" | "downloading" | "failed" | "completed";
  model_id?: string | null;
  filename?: string | null;
  bytes_total?: number | null;
  bytes_downloaded: number;
  started_at?: number | null;
  finished_at?: number | null;
  error?: string | null;
};

export default function ModelsPage() {
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [installed, setInstalled] = useState<InstalledItem[]>([]);
  const [download, setDownload] = useState<DownloadStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshAll() {
    try {
      setError(null);
      const [c, i, d] = await Promise.all([
        apiGet<{ items: CatalogItem[] }>("/api/models/catalog"),
        apiGet<{ items: InstalledItem[] }>("/api/models/installed"),
        apiGet<DownloadStatus>("/api/models/downloads/status"),
      ]);
      setCatalog(c.items);
      setInstalled(i.items);
      setDownload(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void refreshAll();
    const t = window.setInterval(() => {
      void refreshAll();
    }, 1200);
    return () => window.clearInterval(t);
  }, []);

  async function startDownload(modelId: string) {
    try {
      setError(null);
      await apiPost("/api/models/downloads/start", { model_id: modelId });
      await refreshAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  const progressPct = useMemo(() => {
    const total = download?.bytes_total ?? null;
    const done = download?.bytes_downloaded ?? 0;
    if (!total || total <= 0) return null;
    return Math.max(0, Math.min(100, Math.round((done / total) * 100)));
  }, [download]);

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <div className="mx-auto w-full max-w-5xl px-6 py-10">
        <div className="flex items-start justify-between gap-6">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Model Manager</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
              MVP: catalog + installed scan + one download at a time (progress + logs later).
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Home
            </Link>
            <button
              type="button"
              onClick={() => void refreshAll()}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Refresh
            </button>
          </div>
        </div>

        {error ? (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        ) : null}

        <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="flex items-center justify-between gap-4">
            <div className="text-sm">
              <div className="font-medium">Download status: {download?.state ?? "-"}</div>
              <div className="mt-1 text-zinc-600">
                {download?.model_id ? `Model: ${download.model_id}` : "No active download"}
                {download?.error ? ` · Error: ${download.error}` : ""}
              </div>
            </div>
            <div className="w-64">
              <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-100">
                <div
                  className="h-2 rounded-full bg-zinc-900 transition-[width]"
                  style={{ width: `${progressPct ?? 0}%` }}
                />
              </div>
              <div className="mt-2 text-right text-xs text-zinc-500">
                {progressPct !== null ? `${progressPct}%` : "-"}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <div className="text-sm font-semibold">Catalog</div>
            <div className="mt-3 space-y-3">
              {catalog.length === 0 ? (
                <div className="text-sm text-zinc-600">(empty)</div>
              ) : (
                catalog.map((m) => (
                  <div key={m.id} className="rounded-lg border border-zinc-200 p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="text-sm font-semibold">{m.name}</div>
                        <div className="mt-1 text-xs text-zinc-500">
                          {m.type} · {m.filename}
                        </div>
                        {m.notes ? (
                          <div className="mt-2 text-xs text-zinc-600">{m.notes}</div>
                        ) : null}
                      </div>
                      <button
                        type="button"
                        disabled={download?.state === "downloading"}
                        onClick={() => void startDownload(m.id)}
                        className="rounded-lg bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Download
                      </button>
                    </div>
                    <div className="mt-3 break-all text-xs text-zinc-500">{m.url}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <div className="text-sm font-semibold">Installed</div>
            <div className="mt-3 space-y-2">
              {installed.length === 0 ? (
                <div className="text-sm text-zinc-600">(no files yet)</div>
              ) : (
                installed.map((f) => (
                  <div key={f.path} className="flex items-center justify-between rounded-md border border-zinc-200 px-3 py-2">
                    <div className="text-xs text-zinc-700">{f.path}</div>
                    <div className="text-xs text-zinc-500">
                      {(f.size_bytes / (1024 * 1024)).toFixed(1)} MB
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
