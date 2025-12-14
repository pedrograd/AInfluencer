"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { API_BASE_URL, apiGet, apiPost } from "@/lib/api";

type CatalogItem = {
  id: string;
  name: string;
  type: string;
  tier?: number | null;
  tags?: string[] | null;
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
  id: string;
  model_id: string;
  filename: string;
  state: "queued" | "downloading" | "cancelled" | "failed" | "completed";
  bytes_total?: number | null;
  bytes_downloaded: number;
  created_at: number;
  started_at?: number | null;
  finished_at?: number | null;
  error?: string | null;
  cancel_requested?: boolean;
};

export default function ModelsPage() {
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [installed, setInstalled] = useState<InstalledItem[]>([]);
  const [active, setActive] = useState<DownloadStatus | null>(null);
  const [queue, setQueue] = useState<DownloadStatus[]>([]);
  const [history, setHistory] = useState<DownloadStatus[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [verifyingPath, setVerifyingPath] = useState<string | null>(null);
  const [verified, setVerified] = useState<Record<string, string>>({});

  async function refreshAll() {
    try {
      setError(null);
      const [c, i, a, q, h] = await Promise.all([
        apiGet<{ items: CatalogItem[] }>("/api/models/catalog"),
        apiGet<{ items: InstalledItem[] }>("/api/models/installed"),
        apiGet<{ item: DownloadStatus | null }>("/api/models/downloads/active"),
        apiGet<{ items: DownloadStatus[] }>("/api/models/downloads/queue"),
        apiGet<{ items: DownloadStatus[] }>("/api/models/downloads/items"),
      ]);
      setCatalog(c.items);
      setInstalled(i.items);
      setActive(a.item);
      setQueue(q.items);
      setHistory(h.items);
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

  async function enqueue(modelId: string) {
    try {
      setError(null);
      await apiPost("/api/models/downloads/enqueue", { model_id: modelId });
      await refreshAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function cancel(downloadId: string) {
    try {
      setError(null);
      await apiPost("/api/models/downloads/cancel", { download_id: downloadId });
      await refreshAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function importModel(file: File, modelType: string) {
    setImporting(true);
    try {
      setError(null);
      const form = new FormData();
      form.append("file", file);
      form.append("model_type", modelType);

      const res = await fetch(`${API_BASE_URL}/api/models/import`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`Import failed: ${res.status} ${txt}`);
      }
      await refreshAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setImporting(false);
    }
  }

  async function verifyInstalled(path: string) {
    setVerifyingPath(path);
    try {
      setError(null);
      const res = await apiPost<{ ok: boolean; item: { path: string; sha256: string } }>(
        "/api/models/verify",
        { path },
      );
      setVerified((prev) => ({ ...prev, [path]: res.item.sha256 }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setVerifyingPath(null);
    }
  }

  const progressPct = useMemo(() => {
    const total = active?.bytes_total ?? null;
    const done = active?.bytes_downloaded ?? 0;
    if (!total || total <= 0) return null;
    return Math.max(0, Math.min(100, Math.round((done / total) * 100)));
  }, [active]);

  const filteredCatalog = useMemo(() => {
    const q = query.trim().toLowerCase();
    return catalog.filter((m) => {
      if (typeFilter !== "all" && m.type !== typeFilter) return false;
      if (!q) return true;
      const hay = [m.id, m.name, m.filename, ...(m.tags ?? [])].join(" ").toLowerCase();
      return hay.includes(q);
    });
  }, [catalog, query, typeFilter]);

  const installedSet = useMemo(() => {
    // For catalog items we only need a fast "is installed" check.
    return new Set(installed.map((i) => i.path.split("/").slice(-1)[0] ?? i.path));
  }, [installed]);

  const queuedModelIds = useMemo(() => new Set(queue.map((q) => q.model_id)), [queue]);

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
              <div className="font-medium">Active download: {active?.state ?? "idle"}</div>
              <div className="mt-1 text-zinc-600">
                {active?.model_id ? `Model: ${active.model_id}` : "No active download"}
                {active?.error ? ` · Error: ${active.error}` : ""}
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
          {active ? (
            <div className="mt-4 flex items-center justify-between rounded-lg border border-zinc-200 px-3 py-2">
              <div className="text-xs text-zinc-700">
                {active.filename} {active.cancel_requested ? "(cancelling…)" : ""}
              </div>
              <button
                type="button"
                onClick={() => void cancel(active.id)}
                className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
              >
                Cancel
              </button>
            </div>
          ) : null}
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <div className="flex items-center justify-between gap-4">
              <div className="text-sm font-semibold">Catalog</div>
              <div className="flex items-center gap-2">
                <div className="hidden items-center gap-2 sm:flex">
                  {[
                    ["all", "All"],
                    ["checkpoint", "Checkpoints"],
                    ["lora", "LoRAs"],
                    ["embedding", "Embeddings"],
                    ["controlnet", "ControlNet"],
                    ["other", "Other"],
                  ].map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setTypeFilter(key)}
                      className={[
                        "rounded-lg border px-3 py-2 text-sm font-medium",
                        key === typeFilter
                          ? "border-zinc-900 bg-zinc-900 text-white"
                          : "border-zinc-200 bg-white text-zinc-800 hover:bg-zinc-50",
                      ].join(" ")}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search…"
                  className="w-44 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                />
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                >
                  <option value="all">all</option>
                  <option value="checkpoint">checkpoint</option>
                  <option value="lora">lora</option>
                  <option value="embedding">embedding</option>
                  <option value="controlnet">controlnet</option>
                  <option value="other">other</option>
                </select>
              </div>
            </div>
            <div className="mt-3 space-y-3">
              {filteredCatalog.length === 0 ? (
                <div className="text-sm text-zinc-600">(empty)</div>
              ) : (
                filteredCatalog.map((m) => (
                  (() => {
                    const isInstalled = installedSet.has(m.filename);
                    const isQueued = queuedModelIds.has(m.id);
                    const isActive = active?.model_id === m.id;
                    const disabled = isInstalled || isQueued || isActive;
                    const badge = isInstalled ? "Installed" : isActive ? "Downloading" : isQueued ? "Queued" : null;
                    return (
                  <div key={m.id} className="rounded-lg border border-zinc-200 p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="text-sm font-semibold">{m.name}</div>
                        <div className="mt-1 text-xs text-zinc-500">
                          {m.type} · {m.filename}
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-zinc-600">
                          {m.tier ? <span className="rounded bg-zinc-100 px-2 py-1">Tier {m.tier}</span> : null}
                          {(m.tags ?? []).map((t) => (
                            <span key={`${m.id}-${t}`} className="rounded bg-zinc-100 px-2 py-1">
                              {t}
                            </span>
                          ))}
                          {badge ? <span className="rounded bg-emerald-50 px-2 py-1 text-emerald-800">{badge}</span> : null}
                        </div>
                        {m.sha256 ? (
                          <div className="mt-2 break-all text-[11px] text-zinc-500">sha256: {m.sha256}</div>
                        ) : null}
                        {m.notes ? (
                          <div className="mt-2 text-xs text-zinc-600">{m.notes}</div>
                        ) : null}
                      </div>
                      <button
                        type="button"
                        disabled={disabled}
                        onClick={() => void enqueue(m.id)}
                        className="rounded-lg bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isInstalled ? "Installed" : isActive ? "Downloading…" : isQueued ? "Queued" : "Add to queue"}
                      </button>
                    </div>
                    <div className="mt-3 break-all text-xs text-zinc-500">{m.url}</div>
                  </div>
                    );
                  })()
                ))
              )}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <div className="text-sm font-semibold">Queue</div>
            <div className="mt-3 space-y-2">
              {queue.length === 0 ? (
                <div className="text-sm text-zinc-600">(empty)</div>
              ) : (
                queue.map((it) => (
                  <div
                    key={it.id}
                    className="flex items-center justify-between rounded-md border border-zinc-200 px-3 py-2"
                  >
                    <div className="min-w-0">
                      <div className="truncate text-xs font-medium text-zinc-800">{it.model_id}</div>
                      <div className="truncate text-xs text-zinc-500">{it.filename}</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => void cancel(it.id)}
                      className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
                    >
                      Remove
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="flex items-center justify-between gap-4">
            <div className="text-sm font-semibold">Import model file</div>
            <div className="text-xs text-zinc-500">Uploads to your local `.ainfluencer/models/`</div>
          </div>
          <form
            className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center"
            onSubmit={(e) => {
              e.preventDefault();
              const form = e.currentTarget;
              const fileInput = form.elements.namedItem("file") as HTMLInputElement | null;
              const typeInput = form.elements.namedItem("model_type") as HTMLSelectElement | null;
              const file = fileInput?.files?.[0];
              const t = typeInput?.value ?? "other";
              if (!file) return;
              void importModel(file, t);
            }}
          >
            <input
              name="file"
              type="file"
              className="block w-full text-sm"
              accept=".safetensors,.ckpt,.pt,.pth,.bin,.zip"
            />
            <select
              name="model_type"
              defaultValue="other"
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
            >
              <option value="checkpoint">checkpoint</option>
              <option value="lora">lora</option>
              <option value="embedding">embedding</option>
              <option value="controlnet">controlnet</option>
              <option value="other">other</option>
            </select>
            <button
              type="submit"
              disabled={importing}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {importing ? "Importing…" : "Import"}
            </button>
          </form>
        </div>

        <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="text-sm font-semibold">Download history</div>
          <div className="mt-3 space-y-2">
            {history.length === 0 ? (
              <div className="text-sm text-zinc-600">(no history yet)</div>
            ) : (
              history.slice(0, 20).map((it) => (
                <div key={it.id} className="rounded-md border border-zinc-200 px-3 py-2">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="truncate text-xs font-medium text-zinc-800">{it.model_id}</div>
                      <div className="truncate text-xs text-zinc-500">{it.filename}</div>
                    </div>
                    <div className="text-xs text-zinc-600">{it.state}</div>
                  </div>
                  {it.error ? <div className="mt-1 text-xs text-red-700">{it.error}</div> : null}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="text-sm font-semibold">Installed</div>
          <div className="mt-3 space-y-2">
            {installed.length === 0 ? (
              <div className="text-sm text-zinc-600">(no files yet)</div>
            ) : (
              installed.map((f) => (
                <div
                  key={f.path}
                  className="flex items-center justify-between rounded-md border border-zinc-200 px-3 py-2"
                >
                  <div className="min-w-0">
                    <div className="truncate text-xs text-zinc-700">{f.path}</div>
                    {verified[f.path] ? (
                      <div className="mt-1 break-all text-[11px] text-zinc-500">sha256: {verified[f.path]}</div>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-xs text-zinc-500">
                      {(f.size_bytes / (1024 * 1024)).toFixed(1)} MB
                    </div>
                    <button
                      type="button"
                      disabled={verifyingPath === f.path}
                      onClick={() => void verifyInstalled(f.path)}
                      className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {verifyingPath === f.path ? "Verifying…" : "Verify"}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
