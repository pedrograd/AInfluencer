"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { API_BASE_URL, apiGet, apiPost } from "@/lib/api";
import {
  PageHeader,
  SectionCard,
  PrimaryButton,
  SecondaryButton,
  IconButton,
  StatusChip,
  Alert,
  ErrorBanner,
  LoadingSkeleton,
} from "@/components/ui";
import {
  Home,
  RefreshCw,
  Play,
  Square,
  RotateCw,
  Download,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";

type ManagerStatus = {
  state:
    | "not_installed"
    | "installed"
    | "starting"
    | "running"
    | "stopping"
    | "stopped"
    | "error";
  installed_path: string | null;
  process_id: number | null;
  port: number | null;
  base_url: string | null;
  message: string | null;
  error: string | null;
  last_check: number | null;
  is_installed: boolean;
};

type LogEntry = string;

export default function ComfyUIPage() {
  const [status, setStatus] = useState<ManagerStatus | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isInstalling, setIsInstalling] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  async function refreshStatus() {
    try {
      setError(null);
      const s = await apiGet<ManagerStatus>("/api/comfyui/manager/status");
      setStatus(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function refreshLogs() {
    try {
      const res = await apiGet<{ logs: string[]; count: number }>(
        "/api/comfyui/manager/logs?limit=100"
      );
      setLogs(res.logs ?? []);
    } catch (e) {
      // non-fatal
    }
  }

  async function handleInstall() {
    setIsInstalling(true);
    try {
      setError(null);
      await apiPost("/api/comfyui/manager/install", {});
      await refreshStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsInstalling(false);
    }
  }

  async function handleStart() {
    setIsStarting(true);
    try {
      setError(null);
      await apiPost("/api/comfyui/manager/start", {});
      await refreshStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsStarting(false);
    }
  }

  async function handleStop() {
    setIsStopping(true);
    try {
      setError(null);
      await apiPost("/api/comfyui/manager/stop", {});
      await refreshStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsStopping(false);
    }
  }

  async function handleRestart() {
    setIsRestarting(true);
    try {
      setError(null);
      await apiPost("/api/comfyui/manager/restart", {});
      await refreshStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsRestarting(false);
    }
  }

  async function handleSyncModels() {
    setIsSyncing(true);
    try {
      setError(null);
      await apiPost("/api/comfyui/manager/sync-models", {});
      await refreshStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsSyncing(false);
    }
  }

  useEffect(() => {
    void refreshStatus();
    void refreshLogs();
    const t = window.setInterval(() => {
      void refreshStatus();
      void refreshLogs();
    }, 2000);
    return () => window.clearInterval(t);
  }, []);

  const canStart = status?.state === "installed" || status?.state === "stopped";
  const canStop = status?.state === "running";
  const canRestart = status?.state === "running";

  const getStatusChip = (state: string | null) => {
    if (!state) return "info";
    switch (state) {
      case "running":
        return "success";
      case "error":
        return "error";
      case "starting":
      case "stopping":
        return "warning";
      default:
        return "info";
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        <PageHeader
          title="ComfyUI Manager"
          description="Install, start, stop, and manage ComfyUI from the dashboard. View logs and sync models."
          action={
            <div className="flex gap-2">
              <Link href="/">
                <SecondaryButton size="sm" icon={<Home className="h-4 w-4" />}>
                  Home
                </SecondaryButton>
              </Link>
              <IconButton
                icon={<RefreshCw className="h-4 w-4" />}
                size="md"
                variant="ghost"
                onClick={() => {
                  void refreshStatus();
                  void refreshLogs();
                }}
                aria-label="Refresh status"
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
                onClick: refreshStatus,
              }}
            />
          </div>
        )}

        {/* Status Card */}
        <SectionCard title="Status" loading={!status} className="mb-6">
          {status ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <StatusChip
                  status={getStatusChip(status.state)}
                  label={status.state}
                />
                {status.message && (
                  <span className="text-sm text-[var(--text-secondary)]">
                    {status.message}
                  </span>
                )}
              </div>

              {status.error && <Alert message={status.error} variant="error" />}

              <div className="grid gap-3 sm:grid-cols-2">
                {status.installed_path && (
                  <div>
                    <div className="text-xs font-medium text-[var(--text-secondary)] mb-1">
                      Installed Path
                    </div>
                    <code className="text-xs text-[var(--text-primary)] bg-[var(--bg-surface)] px-2 py-1 rounded">
                      {status.installed_path}
                    </code>
                  </div>
                )}

                {status.base_url && (
                  <div>
                    <div className="text-xs font-medium text-[var(--text-secondary)] mb-1">
                      Base URL
                    </div>
                    <code className="text-xs text-[var(--text-primary)] bg-[var(--bg-surface)] px-2 py-1 rounded">
                      {status.base_url}
                    </code>
                  </div>
                )}

                {status.port && (
                  <div>
                    <div className="text-xs font-medium text-[var(--text-secondary)] mb-1">
                      Port
                    </div>
                    <div className="text-sm text-[var(--text-primary)]">
                      {status.port}
                    </div>
                  </div>
                )}

                {status.process_id && (
                  <div>
                    <div className="text-xs font-medium text-[var(--text-secondary)] mb-1">
                      Process ID
                    </div>
                    <div className="text-sm text-[var(--text-primary)]">
                      {status.process_id}
                    </div>
                  </div>
                )}

                {status.last_check && (
                  <div className="sm:col-span-2">
                    <div className="text-xs font-medium text-[var(--text-secondary)] mb-1">
                      Last Check
                    </div>
                    <div className="text-xs text-[var(--text-muted)]">
                      {new Date(status.last_check * 1000).toLocaleString()}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <LoadingSkeleton variant="card" height="150px" />
          )}
        </SectionCard>

        {/* Actions Card */}
        <SectionCard title="Actions" className="mb-6">
          <div className="flex flex-wrap gap-3">
            {!status?.is_installed ? (
              <PrimaryButton
                onClick={() => void handleInstall()}
                disabled={isInstalling}
                loading={isInstalling}
                icon={<Download className="h-4 w-4" />}
              >
                Install ComfyUI
              </PrimaryButton>
            ) : null}
            {canStart ? (
              <PrimaryButton
                onClick={() => void handleStart()}
                disabled={isStarting}
                loading={isStarting}
                icon={<Play className="h-4 w-4" />}
                className="bg-[var(--success)] hover:bg-[var(--success-hover)]"
              >
                Start
              </PrimaryButton>
            ) : null}
            {canStop ? (
              <PrimaryButton
                onClick={() => void handleStop()}
                disabled={isStopping}
                loading={isStopping}
                icon={<Square className="h-4 w-4" />}
                className="bg-[var(--error)] hover:bg-[var(--error-hover)]"
              >
                Stop
              </PrimaryButton>
            ) : null}
            {canRestart ? (
              <PrimaryButton
                onClick={() => void handleRestart()}
                disabled={isRestarting}
                loading={isRestarting}
                icon={<RotateCw className="h-4 w-4" />}
                className="bg-[var(--warning)] hover:bg-[var(--warning-hover)]"
              >
                Restart
              </PrimaryButton>
            ) : null}
            {status?.is_installed ? (
              <SecondaryButton
                onClick={() => void handleSyncModels()}
                disabled={isSyncing}
                loading={isSyncing}
                icon={<RefreshCw className="h-4 w-4" />}
              >
                Sync Models
              </SecondaryButton>
            ) : null}
          </div>
        </SectionCard>

        {/* Logs Card */}
        <SectionCard
          title="Logs"
          description={`${logs.length} entries`}
          className="mb-6"
        >
          <div className="max-h-[400px] overflow-y-auto rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4 font-mono text-xs">
            {logs.length === 0 ? (
              <div className="text-[var(--text-muted)]">(no logs yet)</div>
            ) : (
              logs.map((log, idx) => {
                const match = log.match(/^\[([^\]]+)\] \[([^\]]+)\] (.+)$/);
                const timestamp = match ? match[1] : "";
                const level = match ? match[2] : "";
                const message = match ? match[3] : log;
                const isError = level === "ERROR" || level === "error";
                const isWarning = level === "WARNING" || level === "warning";
                return (
                  <div key={idx} className="mb-1 break-words">
                    <span className="text-[var(--text-muted)]">
                      {timestamp}
                    </span>
                    <span
                      className={
                        isError
                          ? "ml-2 text-[var(--error)]"
                          : isWarning
                          ? "ml-2 text-[var(--warning)]"
                          : "ml-2 text-[var(--text-primary)]"
                      }
                    >
                      [{level}] {message}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </SectionCard>
      </main>
    </div>
  );
}
