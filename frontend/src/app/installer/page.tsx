"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { API_BASE_URL, apiGet, apiPost } from "@/lib/api";
import {
  PageHeader,
  SectionCard,
  PrimaryButton,
  SecondaryButton,
  StatusChip,
  ProgressIndicator,
  Alert,
  ErrorBanner,
  LoadingSkeleton,
} from "@/components/ui";
import {
  RefreshCw,
  CheckCircle2,
  Download,
  Wrench,
  Play,
  AlertTriangle,
  Info,
} from "lucide-react";

type InstallerStatus = {
  state: "idle" | "running" | "failed" | "succeeded";
  step: string | null;
  message: string | null;
  progress: number;
  started_at?: number | null;
  finished_at?: number | null;
};

type InstallerLogItem = {
  ts: number;
  level: string;
  message: string;
  [key: string]: unknown;
};

type SystemCheck = {
  ts: number;
  os: { system: string; release: string; version: string; machine: string };
  python: {
    executable: string;
    version: string;
    supported: boolean;
    supported_versions: string[];
  };
  tools: {
    node: { found: boolean; path: string | null };
    git: { found: boolean; path: string | null };
  };
  resources: {
    disk_total_gb: number;
    disk_free_gb: number;
    ram_total_gb: number | null;
  };
  gpu: {
    nvidia_smi: boolean;
    nvidia_smi_path: string | null;
    nvidia_smi_output: string | null;
  };
  issues?: Array<{
    code: string;
    severity: "error" | "warn" | "info";
    title: string;
    detail: string;
    fix?: {
      summary?: string;
      fix_action?: string;
      repo_scripts?: Array<{ os: string; path: string }>;
    };
  }>;
};

export default function InstallerPage() {
  const [status, setStatus] = useState<InstallerStatus | null>(null);
  const [logs, setLogs] = useState<InstallerLogItem[]>([]);
  const [check, setCheck] = useState<SystemCheck | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [fixingAction, setFixingAction] = useState<string | null>(null);
  const [isRepairing, setIsRepairing] = useState(false);
  const [repairResult, setRepairResult] = useState<{
    checks_run?: boolean;
    venv_repaired?: boolean;
    deps_reinstalled?: boolean;
    ports_checked?: boolean;
    comfyui_checked?: boolean;
    issues_found?: string[];
    issues_fixed?: string[];
  } | null>(null);

  const pollRef = useRef<number | null>(null);

  const isRunning = status?.state === "running";

  const stateLabel = useMemo(() => {
    if (!status) return "Loading…";
    if (status.state === "idle") return "Idle";
    if (status.state === "running") return "Running";
    if (status.state === "succeeded") return "Ready";
    return "Failed";
  }, [status]);

  async function refresh() {
    try {
      setError(null);
      const [s, l] = await Promise.all([
        apiGet<InstallerStatus>("/api/installer/status"),
        apiGet<{ items: InstallerLogItem[] }>("/api/installer/logs"),
      ]);
      setStatus(s);
      setLogs(l.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function runCheck() {
    setIsChecking(true);
    try {
      setError(null);
      const c = await apiGet<SystemCheck>("/api/installer/check");
      setCheck(c);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsChecking(false);
    }
  }

  async function start() {
    setIsStarting(true);
    try {
      setError(null);
      await apiPost("/api/installer/start");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsStarting(false);
    }
  }

  async function runFix(action: string) {
    setFixingAction(action);
    try {
      setError(null);
      await apiPost(`/api/installer/fix/${encodeURIComponent(action)}`);
      await refresh();
      await runCheck();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setFixingAction(null);
    }
  }

  async function fixAll() {
    setFixingAction("fix_all");
    try {
      setError(null);
      await apiPost("/api/installer/fix_all");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setFixingAction(null);
    }
  }

  async function repair() {
    setIsRepairing(true);
    setRepairResult(null);
    try {
      setError(null);
      const result = await apiPost<{
        ok: boolean;
        checks_run?: boolean;
        venv_repaired?: boolean;
        deps_reinstalled?: boolean;
        ports_checked?: boolean;
        comfyui_checked?: boolean;
        issues_found?: string[];
        issues_fixed?: string[];
      }>("/api/installer/repair");
      setRepairResult(result);
      await refresh();
      await runCheck();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsRepairing(false);
    }
  }

  useEffect(() => {
    void refresh();
    void runCheck();
  }, []);

  useEffect(() => {
    if (pollRef.current) window.clearInterval(pollRef.current);
    pollRef.current = window.setInterval(() => {
      void refresh();
    }, 750);

    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const progress = Math.max(0, Math.min(100, status?.progress ?? 0));

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        <PageHeader
          title="Setup AInfluencer"
          description="One-click installer: checks, installs, tests, and logs."
          action={
            <div className="flex flex-wrap items-center gap-2">
              <SecondaryButton
                size="sm"
                icon={<RefreshCw className="h-4 w-4" />}
                onClick={() => void refresh()}
              >
                Refresh
              </SecondaryButton>
              <SecondaryButton
                size="sm"
                icon={<CheckCircle2 className="h-4 w-4" />}
                onClick={() => void runCheck()}
                disabled={isChecking}
                loading={isChecking}
              >
                Run check
              </SecondaryButton>
              <SecondaryButton
                size="sm"
                icon={<Download className="h-4 w-4" />}
                onClick={() =>
                  window.open(
                    `${API_BASE_URL}/api/installer/diagnostics`,
                    "_blank"
                  )
                }
              >
                Diagnostics
              </SecondaryButton>
              {check?.issues?.some((i) => i.fix?.fix_action) && (
                <PrimaryButton
                  size="sm"
                  icon={<Wrench className="h-4 w-4" />}
                  disabled={!!fixingAction || isRunning}
                  loading={fixingAction === "fix_all"}
                  onClick={() => void fixAll()}
                >
                  Fix All
                </PrimaryButton>
              )}
              <PrimaryButton
                size="sm"
                icon={<Wrench className="h-4 w-4" />}
                disabled={isRepairing || isRunning}
                loading={isRepairing}
                onClick={() => void repair()}
                className="bg-[var(--info)] hover:bg-[var(--info)]/90"
              >
                Repair System
              </PrimaryButton>
              <PrimaryButton
                size="sm"
                icon={<Play className="h-4 w-4" />}
                disabled={isStarting || isRunning}
                loading={isStarting || isRunning}
                onClick={() => void start()}
              >
                {isRunning
                  ? "Installing…"
                  : isStarting
                  ? "Starting…"
                  : "Start Installation"}
              </PrimaryButton>
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
                onClick: refresh,
              }}
            />
          </div>
        )}

        {repairResult && (
          <div className="mb-6">
            <Alert
              title="Repair Results"
              message={
                <>
                  {repairResult.issues_fixed &&
                  repairResult.issues_fixed.length > 0 ? (
                    <div className="mb-2">
                      <div className="font-medium text-[var(--success)] mb-1">
                        Fixed:
                      </div>
                      <ul className="ml-4 list-disc space-y-1">
                        {repairResult.issues_fixed.map((issue, i) => (
                          <li key={i}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {repairResult.issues_found &&
                  repairResult.issues_found.length > 0 ? (
                    <div className="mb-2">
                      <div className="font-medium text-[var(--warning)] mb-1">
                        Remaining Issues:
                      </div>
                      <ul className="ml-4 list-disc space-y-1">
                        {repairResult.issues_found.map((issue, i) => (
                          <li key={i}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {(!repairResult.issues_fixed ||
                    repairResult.issues_fixed.length === 0) &&
                  (!repairResult.issues_found ||
                    repairResult.issues_found.length === 0) ? (
                    <div className="text-[var(--success)]">
                      System is healthy - no issues found or fixed.
                    </div>
                  ) : null}
                  <div className="mt-3 text-xs text-[var(--text-muted)]">
                    Checks: {repairResult.checks_run ? "✓" : "✗"} | Venv:{" "}
                    {repairResult.venv_repaired ? "✓ Repaired" : "✓ OK"} | Deps:{" "}
                    {repairResult.deps_reinstalled ? "✓ Reinstalled" : "✓ OK"} |
                    Ports: {repairResult.ports_checked ? "✓ Checked" : "✗"} |
                    ComfyUI: {repairResult.comfyui_checked ? "✓ Checked" : "✗"}
                  </div>
                </>
              }
              variant="info"
            />
          </div>
        )}

        <SectionCard
          title="System Check"
          description={
            check
              ? `${check.os.system} ${check.os.release} · ${check.os.machine}`
              : "Loading system information…"
          }
          action={
            check && (
              <span className="text-xs text-[var(--text-muted)]">
                {new Date(check.ts * 1000).toLocaleString()}
              </span>
            )
          }
          loading={!check && isChecking}
          className="mb-8"
        >
          {check ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4">
                <div className="text-xs font-medium text-[var(--text-secondary)] mb-2">
                  Python
                </div>
                <div className="text-sm">
                  <span
                    className={
                      check.python.supported
                        ? "text-[var(--success)] font-semibold"
                        : "text-[var(--error)] font-semibold"
                    }
                  >
                    {check.python.version}
                  </span>
                  <div className="mt-1 break-all text-xs text-[var(--text-muted)]">
                    {check.python.executable}
                  </div>
                  {!check.python.supported && (
                    <div className="mt-2 text-xs text-[var(--error)]">
                      Requires {check.python.supported_versions.join(" or ")}.
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4">
                <div className="text-xs font-medium text-[var(--text-secondary)] mb-2">
                  Tools
                </div>
                <div className="space-y-1 text-sm">
                  <div>
                    Node:{" "}
                    <StatusChip
                      status={check.tools.node.found ? "success" : "error"}
                      label={check.tools.node.found ? "found" : "missing"}
                    />
                  </div>
                  <div>
                    Git:{" "}
                    <StatusChip
                      status={check.tools.git.found ? "success" : "error"}
                      label={check.tools.git.found ? "found" : "missing"}
                    />
                  </div>
                  <div className="pt-1 text-xs text-[var(--text-muted)]">
                    Disk free: {check.resources.disk_free_gb} GB · RAM:{" "}
                    {check.resources.ram_total_gb ?? "?"} GB
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4 sm:col-span-2">
                <div className="text-xs font-medium text-[var(--text-secondary)] mb-2">
                  GPU (best effort)
                </div>
                <div className="text-sm text-[var(--text-primary)]">
                  {check.gpu.nvidia_smi ? (
                    <div className="space-y-2">
                      <div className="text-[var(--success)] font-medium">
                        nvidia-smi detected
                      </div>
                      <div className="break-all text-xs text-[var(--text-muted)]">
                        {check.gpu.nvidia_smi_path}
                      </div>
                      {check.gpu.nvidia_smi_output && (
                        <pre className="mt-2 overflow-auto rounded-md bg-[var(--bg-base)] border border-[var(--border-base)] p-3 text-xs text-[var(--text-primary)] font-mono">
                          {check.gpu.nvidia_smi_output}
                        </pre>
                      )}
                    </div>
                  ) : (
                    <div className="text-[var(--text-secondary)]">
                      No NVIDIA GPU detected via nvidia-smi.
                    </div>
                  )}
                </div>
              </div>

              {(check.issues?.length ?? 0) > 0 && (
                <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4 sm:col-span-2">
                  <div className="text-xs font-medium text-[var(--text-secondary)] mb-3">
                    Issues & fixes
                  </div>
                  <div className="space-y-3">
                    {check.issues!.map((issue) => (
                      <div
                        key={issue.code}
                        className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] p-4"
                      >
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <div className="flex-1">
                            <div className="text-sm font-semibold text-[var(--text-primary)]">
                              {issue.title}
                            </div>
                            <div className="mt-1 text-sm text-[var(--text-secondary)]">
                              {issue.detail}
                            </div>
                          </div>
                          <StatusChip
                            status={
                              issue.severity === "error"
                                ? "error"
                                : issue.severity === "warn"
                                ? "warning"
                                : "info"
                            }
                            label={issue.severity.toUpperCase()}
                          />
                        </div>

                        {issue.fix?.summary && (
                          <div className="mt-2 text-sm">
                            <span className="font-medium text-[var(--text-primary)]">
                              Fix:
                            </span>{" "}
                            <span className="text-[var(--text-secondary)]">
                              {issue.fix.summary}
                            </span>
                          </div>
                        )}

                        {issue.fix?.fix_action && (
                          <div className="mt-3">
                            <PrimaryButton
                              size="sm"
                              disabled={!!fixingAction}
                              loading={fixingAction === issue.fix.fix_action}
                              onClick={() =>
                                void runFix(issue.fix!.fix_action!)
                              }
                            >
                              {fixingAction === issue.fix.fix_action
                                ? "Fixing…"
                                : "Fix automatically"}
                            </PrimaryButton>
                          </div>
                        )}

                        {(issue.fix?.repo_scripts?.length ?? 0) > 0 && (
                          <div className="mt-2 text-xs text-[var(--text-muted)]">
                            Repo scripts:
                            <ul className="mt-1 list-disc pl-5">
                              {issue.fix!.repo_scripts!.map((s) => (
                                <li key={`${issue.code}-${s.os}`}>
                                  {s.os}:{" "}
                                  <code className="rounded bg-[var(--bg-surface)] px-1 py-0.5 text-[var(--text-primary)]">
                                    {s.path}
                                  </code>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </SectionCard>

        <SectionCard
          title="Installation Status"
          description={`Step: ${status?.step ?? "-"} · ${
            status?.message ?? "-"
          }`}
          action={
            status && (
              <StatusChip
                status={
                  status.state === "succeeded"
                    ? "success"
                    : status.state === "failed"
                    ? "error"
                    : status.state === "running"
                    ? "info"
                    : "warning"
                }
                label={stateLabel}
              />
            )
          }
          className="mb-8"
        >
          <ProgressIndicator
            variant="linear"
            value={progress}
            label={`${progress}%`}
          />
        </SectionCard>

        <SectionCard
          title="Installation Logs"
          description={`Showing last ${logs.length} log entries`}
          className="mb-8"
        >
          <div className="max-h-[420px] overflow-auto rounded-lg border border-[var(--border-base)] bg-[var(--bg-base)] p-4">
            <pre className="text-xs leading-5 text-[var(--text-primary)] font-mono">
              {logs.length === 0
                ? "(no logs yet)"
                : logs
                    .map((l) => {
                      const ts = new Date(l.ts * 1000).toISOString();
                      const level = String(l.level ?? "info").toUpperCase();
                      return `${ts} [${level}] ${l.message}`;
                    })
                    .join("\n")}
            </pre>
          </div>
        </SectionCard>
      </main>
    </div>
  );
}
