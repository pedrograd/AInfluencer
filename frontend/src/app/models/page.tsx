"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL, apiGet, apiPost } from "@/lib/api";
import {
  PageHeader,
  SectionCard,
  PrimaryButton,
  SecondaryButton,
  IconButton,
  Input,
  Select,
  StatusChip,
  Alert,
  ErrorBanner,
  LoadingSkeleton,
  EmptyState,
  ProgressIndicator,
  FormGroup,
} from "@/components/ui";
import {
  Home,
  RefreshCw,
  Download,
  X,
  Plus,
  Upload,
  CheckCircle2,
  Package,
  Search,
  Filter,
  Edit,
  Trash2,
} from "lucide-react";

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
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<{
    synced: number;
    skipped: number;
    errors: string[];
  } | null>(null);

  const [customName, setCustomName] = useState("");
  const [customType, setCustomType] = useState("other");
  const [customUrl, setCustomUrl] = useState("");
  const [customFilename, setCustomFilename] = useState("");
  const [addingCustom, setAddingCustom] = useState(false);
  const [customList, setCustomList] = useState<CatalogItem[]>([]);
  const [editingCustomId, setEditingCustomId] = useState<string | null>(null);
  const [editingCustom, setEditingCustom] = useState<{
    name: string;
    type: string;
    url: string;
    filename: string;
    tier: number;
  } | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  function normalizeUrlAndFilename(raw: string): {
    url: string;
    filename: string | null;
  } {
    try {
      const u = new URL(raw.trim());

      if (u.hostname === "huggingface.co") {
        u.pathname = u.pathname.replace("/blob/", "/resolve/");
      }

      if (u.hostname === "civitai.com") {
        const mv = u.searchParams.get("modelVersionId");
        if (mv) {
          return {
            url: `https://civitai.com/api/download/models/${mv}`,
            filename: null,
          };
        }
      }

      const base = u.pathname.split("/").pop() || "";
      return { url: u.toString(), filename: base || null };
    } catch {
      return { url: raw, filename: null };
    }
  }

  async function refreshAll() {
    try {
      setError(null);
      const [c, i, a, q, h, cc] = await Promise.all([
        apiGet<{ items: CatalogItem[] }>("/api/models/catalog"),
        apiGet<{ items: InstalledItem[] }>("/api/models/installed"),
        apiGet<{ item: DownloadStatus | null }>("/api/models/downloads/active"),
        apiGet<{ items: DownloadStatus[] }>("/api/models/downloads/queue"),
        apiGet<{ items: DownloadStatus[] }>("/api/models/downloads/items"),
        apiGet<{ items: CatalogItem[] }>("/api/models/catalog/custom"),
      ]);
      setCatalog(c.items);
      setInstalled(i.items);
      setActive(a.item);
      setQueue(q.items);
      setHistory(h.items);
      setCustomList(cc.items);
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
      await apiPost("/api/models/downloads/cancel", {
        download_id: downloadId,
      });
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
      const res = await apiPost<{
        ok: boolean;
        item: { path: string; sha256: string };
      }>("/api/models/verify", { path });
      setVerified((prev) => ({ ...prev, [path]: res.item.sha256 }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setVerifyingPath(null);
    }
  }

  async function syncModels() {
    setIsSyncing(true);
    setSyncMessage(null);
    setSyncResult(null);
    try {
      setError(null);
      const res = await apiPost<{
        ok: boolean;
        synced: number;
        skipped: number;
        errors: string[];
      }>("/api/comfyui/manager/sync-models", {});
      setSyncResult({
        synced: res.synced,
        skipped: res.skipped,
        errors: res.errors,
      });
      if (res.errors.length === 0) {
        setSyncMessage("Models synced successfully to ComfyUI!");
      } else {
        setSyncMessage(
          `Synced ${res.synced} model(s) with ${res.errors.length} error(s)`
        );
      }
      setTimeout(() => setSyncMessage(null), 10000);
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : String(e);
      setError(errorMsg);
      setSyncMessage(`Sync failed: ${errorMsg}`);
      setTimeout(() => setSyncMessage(null), 5000);
    } finally {
      setIsSyncing(false);
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
      const hay = [m.id, m.name, m.filename, ...(m.tags ?? [])]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [catalog, query, typeFilter]);

  const recommendedCatalog = useMemo(() => {
    return filteredCatalog.filter((m) => (m.tier ?? 3) <= 2);
  }, [filteredCatalog]);

  const installedSet = useMemo(() => {
    return new Set(
      installed.map((i) => i.path.split("/").slice(-1)[0] ?? i.path)
    );
  }, [installed]);

  const queuedModelIds = useMemo(
    () => new Set(queue.map((q) => q.model_id)),
    [queue]
  );

  const getStatusChip = (state: string) => {
    switch (state) {
      case "completed":
        return "success";
      case "failed":
        return "error";
      case "downloading":
        return "info";
      case "queued":
        return "warning";
      default:
        return "info";
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        <PageHeader
          title="Model Manager"
          description="Browse catalog, download models, and manage your installed models"
          action={
            <div className="flex gap-2">
              <Link href="/">
                <SecondaryButton size="sm" icon={<Home className="h-4 w-4" />}>
                  Home
                </SecondaryButton>
              </Link>
              <SecondaryButton
                size="sm"
                onClick={() => void syncModels()}
                disabled={isSyncing}
                loading={isSyncing}
                icon={<RefreshCw className="h-4 w-4" />}
              >
                Sync to ComfyUI
              </SecondaryButton>
              <IconButton
                icon={<RefreshCw className="h-4 w-4" />}
                size="md"
                variant="ghost"
                onClick={() => void refreshAll()}
                aria-label="Refresh"
              />
            </div>
          }
        />

        {error && (
          <div className="mb-6">
            <ErrorBanner
              title="Error"
              message={error}
              remediation={{
                label: "Retry",
                onClick: refreshAll,
              }}
            />
          </div>
        )}

        {syncResult && (
          <div className="mb-6">
            <Alert
              title="Sync Results"
              message={`Synced: ${syncResult.synced} model(s), Skipped: ${
                syncResult.skipped
              } model(s)${
                syncResult.errors.length > 0
                  ? `, Errors: ${syncResult.errors.length}`
                  : ""
              }`}
              variant={syncResult.errors.length > 0 ? "warning" : "success"}
              dismissible
              onDismiss={() => setSyncResult(null)}
            />
            {syncResult.errors.length > 0 && (
              <div className="mt-2 text-xs text-[var(--text-secondary)]">
                {syncResult.errors.map((err, idx) => (
                  <div key={idx}>{err}</div>
                ))}
              </div>
            )}
          </div>
        )}

        {syncMessage && (
          <div className="mb-6">
            <Alert
              message={syncMessage}
              variant={
                syncMessage.includes("successfully") ? "success" : "error"
              }
              dismissible
              onDismiss={() => setSyncMessage(null)}
            />
          </div>
        )}

        {/* Active Download */}
        {active && (
          <SectionCard
            title="Active Download"
            description={active.filename}
            className="mb-6"
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <StatusChip
                  status={getStatusChip(active.state)}
                  label={active.state}
                />
                {active.cancel_requested && (
                  <span className="text-xs text-[var(--text-muted)]">
                    (cancelling…)
                  </span>
                )}
              </div>
              {progressPct !== null && (
                <ProgressIndicator
                  variant="linear"
                  value={progressPct}
                  label={`${progressPct}%`}
                />
              )}
              {active.error && <Alert message={active.error} variant="error" />}
              <SecondaryButton
                onClick={() => void cancel(active.id)}
                disabled={active.cancel_requested}
                size="sm"
                icon={<X className="h-4 w-4" />}
              >
                Cancel Download
              </SecondaryButton>
            </div>
          </SectionCard>
        )}

        <div className="grid gap-6 lg:grid-cols-2 mb-6">
          {/* Catalog */}
          <SectionCard
            title="Catalog"
            description={`${filteredCatalog.length} model(s) available`}
            action={
              <div className="flex items-center gap-2">
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search…"
                  icon={<Search className="h-4 w-4" />}
                  className="w-44"
                />
                <Select
                  options={[
                    { value: "all", label: "All" },
                    { value: "checkpoint", label: "Checkpoints" },
                    { value: "lora", label: "LoRAs" },
                    { value: "embedding", label: "Embeddings" },
                    { value: "controlnet", label: "ControlNet" },
                    { value: "other", label: "Other" },
                  ]}
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-36"
                />
              </div>
            }
            loading={catalog.length === 0}
            empty={filteredCatalog.length === 0}
            emptyMessage="No models found"
          >
            <div className="space-y-4">
              {recommendedCatalog.length > 0 && (
                <div>
                  <div className="mb-3 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                    Recommended
                  </div>
                  <div className="space-y-3">
                    {recommendedCatalog.map((m) => {
                      const isInstalled = installedSet.has(m.filename);
                      const isQueued = queuedModelIds.has(m.id);
                      const isActive = active?.model_id === m.id;
                      const disabled = isInstalled || isQueued || isActive;
                      const badge = isInstalled
                        ? "Installed"
                        : isActive
                        ? "Downloading"
                        : isQueued
                        ? "Queued"
                        : null;
                      return (
                        <div
                          key={m.id}
                          className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] p-4"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-semibold text-[var(--text-primary)]">
                                {m.name}
                              </div>
                              <div className="mt-1 text-xs text-[var(--text-secondary)]">
                                {m.type} · {m.filename}
                              </div>
                              <div className="mt-2 flex flex-wrap gap-2">
                                {m.tier && (
                                  <StatusChip
                                    status="info"
                                    label={`Tier ${m.tier}`}
                                    className="text-[10px]"
                                  />
                                )}
                                {(m.tags ?? []).map((t) => (
                                  <StatusChip
                                    key={`${m.id}-${t}`}
                                    status="info"
                                    label={t}
                                    className="text-[10px]"
                                  />
                                ))}
                                {badge && (
                                  <StatusChip
                                    status={
                                      isInstalled
                                        ? "success"
                                        : isActive
                                        ? "info"
                                        : "warning"
                                    }
                                    label={badge}
                                    className="text-[10px]"
                                  />
                                )}
                              </div>
                              {m.sha256 && (
                                <div className="mt-2 break-all text-[11px] text-[var(--text-muted)] font-mono">
                                  sha256: {m.sha256}
                                </div>
                              )}
                              {m.notes && (
                                <div className="mt-2 text-xs text-[var(--text-secondary)]">
                                  {m.notes}
                                </div>
                              )}
                            </div>
                            <PrimaryButton
                              onClick={() => void enqueue(m.id)}
                              disabled={disabled}
                              size="sm"
                              icon={<Download className="h-4 w-4" />}
                            >
                              {isInstalled
                                ? "Installed"
                                : isActive
                                ? "Downloading…"
                                : isQueued
                                ? "Queued"
                                : "Add to queue"}
                            </PrimaryButton>
                          </div>
                          <div className="mt-3 break-all text-xs text-[var(--text-muted)]">
                            {m.url}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {filteredCatalog.length > recommendedCatalog.length && (
                <div>
                  <div className="mb-3 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                    All Models
                  </div>
                  <div className="space-y-3">
                    {filteredCatalog
                      .filter((m) => (m.tier ?? 3) > 2)
                      .map((m) => {
                        const isInstalled = installedSet.has(m.filename);
                        const isQueued = queuedModelIds.has(m.id);
                        const isActive = active?.model_id === m.id;
                        const disabled = isInstalled || isQueued || isActive;
                        const badge = isInstalled
                          ? "Installed"
                          : isActive
                          ? "Downloading"
                          : isQueued
                          ? "Queued"
                          : null;
                        return (
                          <div
                            key={m.id}
                            className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] p-4"
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-semibold text-[var(--text-primary)]">
                                  {m.name}
                                </div>
                                <div className="mt-1 text-xs text-[var(--text-secondary)]">
                                  {m.type} · {m.filename}
                                </div>
                                <div className="mt-2 flex flex-wrap gap-2">
                                  {m.tier && (
                                    <StatusChip
                                      status="info"
                                      label={`Tier ${m.tier}`}
                                      className="text-[10px]"
                                    />
                                  )}
                                  {(m.tags ?? []).map((t) => (
                                    <StatusChip
                                      key={`${m.id}-${t}`}
                                      status="info"
                                      label={t}
                                      className="text-[10px]"
                                    />
                                  ))}
                                  {badge && (
                                    <StatusChip
                                      status={
                                        isInstalled
                                          ? "success"
                                          : isActive
                                          ? "info"
                                          : "warning"
                                      }
                                      label={badge}
                                      className="text-[10px]"
                                    />
                                  )}
                                </div>
                                {m.sha256 && (
                                  <div className="mt-2 break-all text-[11px] text-[var(--text-muted)] font-mono">
                                    sha256: {m.sha256}
                                  </div>
                                )}
                                {m.notes && (
                                  <div className="mt-2 text-xs text-[var(--text-secondary)]">
                                    {m.notes}
                                  </div>
                                )}
                              </div>
                              <PrimaryButton
                                onClick={() => void enqueue(m.id)}
                                disabled={disabled}
                                size="sm"
                                icon={<Download className="h-4 w-4" />}
                              >
                                {isInstalled
                                  ? "Installed"
                                  : isActive
                                  ? "Downloading…"
                                  : isQueued
                                  ? "Queued"
                                  : "Add to queue"}
                              </PrimaryButton>
                            </div>
                            <div className="mt-3 break-all text-xs text-[var(--text-muted)]">
                              {m.url}
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}
            </div>
          </SectionCard>

          {/* Queue */}
          <SectionCard
            title="Download Queue"
            description={`${queue.length} item(s) in queue`}
            empty={queue.length === 0}
            emptyMessage="Queue is empty"
          >
            <div className="space-y-2">
              {queue.map((it) => (
                <div
                  key={it.id}
                  className="flex items-center justify-between rounded-md border border-[var(--border-base)] bg-[var(--bg-elevated)] px-3 py-2"
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-xs font-medium text-[var(--text-primary)]">
                      {it.model_id}
                    </div>
                    <div className="truncate text-xs text-[var(--text-secondary)]">
                      {it.filename}
                    </div>
                  </div>
                  <SecondaryButton
                    onClick={() => void cancel(it.id)}
                    size="sm"
                    icon={<X className="h-3 w-3" />}
                  >
                    Remove
                  </SecondaryButton>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        {/* Add Custom Model */}
        <SectionCard
          title="Add Custom Model URL"
          description="Adds to your local catalog and enables queue download"
          className="mb-6"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void (async () => {
                setAddingCustom(true);
                try {
                  setError(null);
                  await apiPost("/api/models/catalog/custom", {
                    name: customName,
                    type: customType,
                    url: customUrl,
                    filename: customFilename,
                    tier: 3,
                    tags: ["custom"],
                  });
                  setCustomName("");
                  setCustomUrl("");
                  setCustomFilename("");
                  setCustomType("other");
                  await refreshAll();
                } catch (e2) {
                  setError(e2 instanceof Error ? e2.message : String(e2));
                } finally {
                  setAddingCustom(false);
                }
              })();
            }}
          >
            <FormGroup>
              <div className="grid gap-4 sm:grid-cols-2">
                <Input
                  label="Name"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  placeholder="e.g. Juggernaut XL v9"
                  required
                />
                <Select
                  label="Type"
                  options={[
                    { value: "checkpoint", label: "Checkpoint" },
                    { value: "lora", label: "LoRA" },
                    { value: "embedding", label: "Embedding" },
                    { value: "controlnet", label: "ControlNet" },
                    { value: "other", label: "Other" },
                  ]}
                  value={customType}
                  onChange={(e) => setCustomType(e.target.value)}
                />
                <Input
                  label="Download URL"
                  value={customUrl}
                  onChange={(e) => {
                    const v = e.target.value;
                    const normalized = normalizeUrlAndFilename(v);
                    setCustomUrl(normalized.url);
                    if (!customFilename && normalized.filename)
                      setCustomFilename(normalized.filename);
                  }}
                  placeholder="Direct download URL (https://...)"
                  type="url"
                  required
                  className="sm:col-span-2"
                />
                <Input
                  label="Filename"
                  value={customFilename}
                  onChange={(e) => setCustomFilename(e.target.value)}
                  placeholder="Auto from URL"
                />
                <div className="flex items-end">
                  <PrimaryButton
                    type="submit"
                    disabled={addingCustom}
                    loading={addingCustom}
                    icon={<Plus className="h-4 w-4" />}
                    className="w-full sm:w-auto"
                  >
                    Add to Catalog
                  </PrimaryButton>
                </div>
              </div>
            </FormGroup>
          </form>
        </SectionCard>

        {/* Custom Catalog */}
        <SectionCard
          title="Custom Catalog"
          description={`${customList.length} custom model(s)`}
          empty={customList.length === 0}
          emptyMessage="No custom models yet"
          className="mb-6"
        >
          <div className="space-y-3">
            {customList.map((m) => (
              <div
                key={m.id}
                className="rounded-md border border-[var(--border-base)] bg-[var(--bg-elevated)] p-4"
              >
                {editingCustomId === m.id && editingCustom ? (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      void (async () => {
                        try {
                          setError(null);
                          const normalized = normalizeUrlAndFilename(
                            editingCustom.url
                          );
                          const payload = {
                            name: editingCustom.name,
                            type: editingCustom.type,
                            url: normalized.url,
                            filename:
                              editingCustom.filename ||
                              normalized.filename ||
                              "",
                            tier: editingCustom.tier,
                            tags: ["custom"],
                          };
                          const res = await fetch(
                            `${API_BASE_URL}/api/models/catalog/custom/${encodeURIComponent(
                              m.id
                            )}`,
                            {
                              method: "PUT",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify(payload),
                            }
                          );
                          if (!res.ok) {
                            const txt = await res.text().catch(() => "");
                            throw new Error(
                              `Update failed: ${res.status} ${txt}`
                            );
                          }
                          setEditingCustomId(null);
                          setEditingCustom(null);
                          await refreshAll();
                        } catch (e4) {
                          setError(
                            e4 instanceof Error ? e4.message : String(e4)
                          );
                        }
                      })();
                    }}
                  >
                    <FormGroup>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <Input
                          label="Name"
                          value={editingCustom.name}
                          onChange={(e) =>
                            setEditingCustom((p) =>
                              p ? { ...p, name: e.target.value } : p
                            )
                          }
                        />
                        <Select
                          label="Type"
                          options={[
                            { value: "checkpoint", label: "Checkpoint" },
                            { value: "lora", label: "LoRA" },
                            { value: "embedding", label: "Embedding" },
                            { value: "controlnet", label: "ControlNet" },
                            { value: "other", label: "Other" },
                          ]}
                          value={editingCustom.type}
                          onChange={(e) =>
                            setEditingCustom((p) =>
                              p ? { ...p, type: e.target.value } : p
                            )
                          }
                        />
                        <Input
                          label="URL"
                          value={editingCustom.url}
                          onChange={(e) =>
                            setEditingCustom((p) =>
                              p ? { ...p, url: e.target.value } : p
                            )
                          }
                          className="sm:col-span-2"
                        />
                        <Input
                          label="Filename"
                          value={editingCustom.filename}
                          onChange={(e) =>
                            setEditingCustom((p) =>
                              p ? { ...p, filename: e.target.value } : p
                            )
                          }
                        />
                        <div className="flex items-end gap-2">
                          <PrimaryButton type="submit" size="sm">
                            Save
                          </PrimaryButton>
                          <SecondaryButton
                            type="button"
                            onClick={() => {
                              setEditingCustomId(null);
                              setEditingCustom(null);
                            }}
                            size="sm"
                          >
                            Cancel
                          </SecondaryButton>
                        </div>
                      </div>
                    </FormGroup>
                  </form>
                ) : (
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-semibold text-[var(--text-primary)]">
                        {m.name}
                      </div>
                      <div className="mt-1 truncate text-xs text-[var(--text-secondary)]">
                        {m.type} · {m.filename} ·{" "}
                        <span className="font-mono">{m.id}</span>
                      </div>
                      <div className="mt-2 break-all text-xs text-[var(--text-muted)]">
                        {m.url}
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <SecondaryButton
                        onClick={() => {
                          setEditingCustomId(m.id);
                          setEditingCustom({
                            name: m.name,
                            type: m.type,
                            url: m.url,
                            filename: m.filename,
                            tier: m.tier ?? 3,
                          });
                        }}
                        size="sm"
                        icon={<Edit className="h-4 w-4" />}
                      >
                        Edit
                      </SecondaryButton>
                      <IconButton
                        icon={<Trash2 className="h-4 w-4" />}
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          void (async () => {
                            try {
                              setError(null);
                              const res = await fetch(
                                `${API_BASE_URL}/api/models/catalog/custom/${encodeURIComponent(
                                  m.id
                                )}`,
                                { method: "DELETE" }
                              );
                              if (!res.ok) {
                                const txt = await res.text().catch(() => "");
                                throw new Error(
                                  `Delete failed: ${res.status} ${txt}`
                                );
                              }
                              await refreshAll();
                            } catch (e3) {
                              setError(
                                e3 instanceof Error ? e3.message : String(e3)
                              );
                            }
                          })();
                        }}
                        aria-label="Delete"
                        className="text-[var(--error)] hover:bg-[var(--error-bg)]"
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </SectionCard>

        {/* Import Model */}
        <SectionCard
          title="Import Model File"
          description="Uploads to your local `.ainfluencer/models/`"
          className="mb-6"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const form = e.currentTarget;
              const fileInput = form.elements.namedItem(
                "file"
              ) as HTMLInputElement | null;
              const typeInput = form.elements.namedItem(
                "model_type"
              ) as HTMLSelectElement | null;
              const file = fileInput?.files?.[0];
              const t = typeInput?.value ?? "other";
              if (!file) return;
              void importModel(file, t);
            }}
          >
            <FormGroup>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                <div className="flex-1">
                  <Input
                    name="file"
                    type="file"
                    label="Model File"
                    accept=".safetensors,.ckpt,.pt,.pth,.bin,.zip"
                    onChange={() => {}}
                  />
                </div>
                <Select
                  name="model_type"
                  label="Type"
                  defaultValue="other"
                  options={[
                    { value: "checkpoint", label: "Checkpoint" },
                    { value: "lora", label: "LoRA" },
                    { value: "embedding", label: "Embedding" },
                    { value: "controlnet", label: "ControlNet" },
                    { value: "other", label: "Other" },
                  ]}
                />
                <PrimaryButton
                  type="submit"
                  disabled={importing}
                  loading={importing}
                  icon={<Upload className="h-4 w-4" />}
                >
                  Import
                </PrimaryButton>
              </div>
            </FormGroup>
          </form>
        </SectionCard>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Download History */}
          <SectionCard
            title="Download History"
            description={`${history.length} item(s)`}
            empty={history.length === 0}
            emptyMessage="No download history yet"
          >
            <div className="space-y-2">
              {history.slice(0, 20).map((it) => (
                <div
                  key={it.id}
                  className="rounded-md border border-[var(--border-base)] bg-[var(--bg-elevated)] px-3 py-2"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-xs font-medium text-[var(--text-primary)]">
                        {it.model_id}
                      </div>
                      <div className="truncate text-xs text-[var(--text-secondary)]">
                        {it.filename}
                      </div>
                    </div>
                    <StatusChip
                      status={getStatusChip(it.state)}
                      label={it.state}
                      className="text-[10px]"
                    />
                  </div>
                  {it.error && (
                    <div className="mt-1 text-xs text-[var(--error)]">
                      {it.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </SectionCard>

          {/* Installed */}
          <SectionCard
            title="Installed Models"
            description={`${installed.length} file(s)`}
            empty={installed.length === 0}
            emptyMessage="No installed models yet"
          >
            <div className="space-y-2">
              {installed.map((f) => (
                <div
                  key={f.path}
                  className="flex items-center justify-between rounded-md border border-[var(--border-base)] bg-[var(--bg-elevated)] px-3 py-2"
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-xs text-[var(--text-primary)]">
                      {f.path}
                    </div>
                    {verified[f.path] && (
                      <div className="mt-1 break-all text-[11px] text-[var(--text-muted)] font-mono">
                        sha256: {verified[f.path]}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-xs text-[var(--text-secondary)]">
                      {(f.size_bytes / (1024 * 1024)).toFixed(1)} MB
                    </div>
                    <SecondaryButton
                      disabled={verifyingPath === f.path}
                      loading={verifyingPath === f.path}
                      onClick={() => void verifyInstalled(f.path)}
                      size="sm"
                    >
                      Verify
                    </SecondaryButton>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      </main>
    </div>
  );
}
