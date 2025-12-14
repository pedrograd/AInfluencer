"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { API_BASE_URL, apiGet, apiPost } from "@/lib/api";

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
  python: { executable: string; version: string; supported: boolean; supported_versions: string[] };
  tools: { node: { found: boolean; path: string | null }; git: { found: boolean; path: string | null } };
  resources: { disk_total_gb: number; disk_free_gb: number; ram_total_gb: number | null };
  gpu: { nvidia_smi: boolean; nvidia_smi_path: string | null; nvidia_smi_output: string | null };
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
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <div className="mx-auto w-full max-w-5xl px-6 py-10">
        <div className="flex items-start justify-between gap-6">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Setup</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
              One-click installer MVP: checks, installs, tests, and logs.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => void refresh()}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Refresh
            </button>
            <button
              type="button"
              onClick={() => void runCheck()}
              disabled={isChecking}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isChecking ? "Checking…" : "Run check"}
            </button>
            <a
              href={`${API_BASE_URL}/api/installer/diagnostics`}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Download diagnostics
            </a>
            {check?.issues?.some((i) => i.fix?.fix_action) ? (
              <button
                type="button"
                disabled={!!fixingAction || isRunning}
                onClick={() => void fixAll()}
                className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {fixingAction === "fix_all" ? "Fixing…" : "Fix everything needed"}
              </button>
            ) : null}
            <button
              type="button"
              disabled={isStarting || isRunning}
              onClick={() => void start()}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isRunning ? "Installing…" : isStarting ? "Starting…" : "Start installation"}
            </button>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="flex items-start justify-between gap-6">
            <div>
              <div className="text-sm font-semibold">System check</div>
              <div className="mt-1 text-sm text-zinc-600">
                {check
                  ? `${check.os.system} ${check.os.release} · ${check.os.machine}`
                  : "Loading…"}
              </div>
            </div>
            <div className="text-right text-xs text-zinc-500">
              {check ? new Date(check.ts * 1000).toLocaleString() : ""}
            </div>
          </div>

          {check ? (
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-zinc-200 p-3">
                <div className="text-xs font-medium text-zinc-500">Python</div>
                <div className="mt-1 text-sm">
                  <span className={check.python.supported ? "text-emerald-700" : "text-red-700"}>
                    {check.python.version}
                  </span>
                  <div className="mt-1 break-all text-xs text-zinc-500">
                    {check.python.executable}
                  </div>
                  {!check.python.supported ? (
                    <div className="mt-2 text-xs text-red-700">
                      Requires {check.python.supported_versions.join(" or ")}.
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="rounded-lg border border-zinc-200 p-3">
                <div className="text-xs font-medium text-zinc-500">Tools</div>
                <div className="mt-2 space-y-1 text-sm">
                  <div>
                    Node:{" "}
                    <span className={check.tools.node.found ? "text-emerald-700" : "text-red-700"}>
                      {check.tools.node.found ? "found" : "missing"}
                    </span>
                  </div>
                  <div>
                    Git:{" "}
                    <span className={check.tools.git.found ? "text-emerald-700" : "text-red-700"}>
                      {check.tools.git.found ? "found" : "missing"}
                    </span>
                  </div>
                  <div className="pt-1 text-xs text-zinc-500">
                    Disk free: {check.resources.disk_free_gb} GB · RAM:{" "}
                    {check.resources.ram_total_gb ?? "?"} GB
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-zinc-200 p-3 sm:col-span-2">
                <div className="text-xs font-medium text-zinc-500">GPU (best effort)</div>
                <div className="mt-2 text-sm text-zinc-700">
                  {check.gpu.nvidia_smi ? (
                    <div className="space-y-1">
                      <div className="text-emerald-700">nvidia-smi detected</div>
                      <div className="break-all text-xs text-zinc-500">{check.gpu.nvidia_smi_path}</div>
                      {check.gpu.nvidia_smi_output ? (
                        <pre className="mt-2 overflow-auto rounded-md bg-zinc-950 p-2 text-xs text-zinc-100">
                          {check.gpu.nvidia_smi_output}
                        </pre>
                      ) : null}
                    </div>
                  ) : (
                    <div className="text-zinc-600">No NVIDIA GPU detected via nvidia-smi.</div>
                  )}
                </div>
              </div>

              {(check.issues?.length ?? 0) > 0 ? (
                <div className="rounded-lg border border-zinc-200 p-3 sm:col-span-2">
                  <div className="text-xs font-medium text-zinc-500">Issues & fixes</div>
                  <div className="mt-2 space-y-3">
                    {check.issues!.map((issue) => (
                      <div key={issue.code} className="rounded-md border border-zinc-200 p-3">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <div className="text-sm font-semibold">{issue.title}</div>
                            <div className="mt-1 text-sm text-zinc-600">{issue.detail}</div>
                          </div>
                          <div
                            className={[
                              "shrink-0 rounded-full px-2 py-1 text-xs font-medium",
                              issue.severity === "error"
                                ? "bg-red-50 text-red-700"
                                : issue.severity === "warn"
                                  ? "bg-amber-50 text-amber-800"
                                  : "bg-zinc-100 text-zinc-700",
                            ].join(" ")}
                          >
                            {issue.severity.toUpperCase()}
                          </div>
                        </div>

                        {issue.fix?.summary ? (
                          <div className="mt-2 text-sm">
                            <span className="font-medium">Fix:</span>{" "}
                            <span className="text-zinc-700">{issue.fix.summary}</span>
                          </div>
                        ) : null}

                        {issue.fix?.fix_action ? (
                          <div className="mt-3">
                            <button
                              type="button"
                              disabled={!!fixingAction}
                              onClick={() => void runFix(issue.fix!.fix_action!)}
                              className="rounded-lg bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              {fixingAction === issue.fix.fix_action ? "Fixing…" : "Fix automatically"}
                            </button>
                          </div>
                        ) : null}

                        {(issue.fix?.repo_scripts?.length ?? 0) > 0 ? (
                          <div className="mt-2 text-xs text-zinc-600">
                            Repo scripts:
                            <ul className="mt-1 list-disc pl-5">
                              {issue.fix!.repo_scripts!.map((s) => (
                                <li key={`${issue.code}-${s.os}`}>
                                  {s.os}: <code className="rounded bg-zinc-100 px-1 py-0.5">{s.path}</code>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className="mt-8 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="flex items-center justify-between gap-4">
            <div className="text-sm">
              <div className="font-medium">Status: {stateLabel}</div>
              <div className="mt-1 text-zinc-600">
                Step: {status?.step ?? "-"} · {status?.message ?? "-"}
              </div>
            </div>
            <div className="w-64">
              <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-100">
                <div
                  className="h-2 rounded-full bg-zinc-900 transition-[width]"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="mt-2 text-right text-xs text-zinc-500">
                {progress}%
              </div>
            </div>
          </div>

          {error ? (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </div>
          ) : null}
        </div>

        <div className="mt-8">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-900">Logs</h2>
            <div className="text-xs text-zinc-500">Showing last {logs.length}</div>
          </div>

          <div className="mt-3 max-h-[420px] overflow-auto rounded-xl border border-zinc-200 bg-black p-3">
            <pre className="text-xs leading-5 text-zinc-100">
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
        </div>
      </div>
    </div>
  );
}
