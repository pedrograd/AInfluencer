"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { API_BASE_URL, apiGet, apiPost } from "@/lib/api";

type ManagerStatus = {
  state: "not_installed" | "installed" | "starting" | "running" | "stopping" | "stopped" | "error";
  installed_path: string | null;
  process_id: number | null;
  port: number | null;
  base_url: string | null;
  message: string | null;
  error: string | null;
  last_check: number | null;
  is_installed: boolean;
};

// Logs are returned as strings in format: "[YYYY-MM-DD HH:MM:SS] [LEVEL] message"
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
      const res = await apiGet<{ logs: string[]; count: number }>("/api/comfyui/manager/logs?limit=100");
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

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <div className="mx-auto w-full max-w-5xl px-6 py-10">
        <div className="flex items-start justify-between gap-6">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">ComfyUI Manager</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
              Install, start, stop, and manage ComfyUI from the dashboard. View logs and sync models.
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
              onClick={() => {
                void refreshStatus();
                void refreshLogs();
              }}
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

        <div className="mt-6 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="text-sm font-semibold">Status</div>
              <div className="mt-2 space-y-1 text-sm text-zinc-700">
                {status ? (
                  <>
                    <div>
                      <span className="font-medium">State:</span>{" "}
                      <span
                        className={
                          status.state === "running"
                            ? "text-emerald-700"
                            : status.state === "error"
                              ? "text-red-700"
                              : "text-zinc-700"
                        }
                      >
                        {status.state}
                      </span>
                    </div>
                    {status.installed_path ? (
                      <div>
                        <span className="font-medium">Installed path:</span>{" "}
                        <code className="rounded bg-zinc-100 px-1 py-0.5 text-xs">{status.installed_path}</code>
                      </div>
                    ) : null}
                    {status.base_url ? (
                      <div>
                        <span className="font-medium">Base URL:</span>{" "}
                        <code className="rounded bg-zinc-100 px-1 py-0.5 text-xs">{status.base_url}</code>
                      </div>
                    ) : null}
                    {status.port ? (
                      <div>
                        <span className="font-medium">Port:</span> {status.port}
                      </div>
                    ) : null}
                    {status.process_id ? (
                      <div>
                        <span className="font-medium">Process ID:</span> {status.process_id}
                      </div>
                    ) : null}
                    {status.message ? (
                      <div>
                        <span className="font-medium">Message:</span> {status.message}
                      </div>
                    ) : null}
                    {status.error ? (
                      <div className="text-red-700">
                        <span className="font-medium">Error:</span> {status.error}
                      </div>
                    ) : null}
                    {status.last_check ? (
                      <div className="text-xs text-zinc-500">
                        Last check: {new Date(status.last_check * 1000).toLocaleString()}
                      </div>
                    ) : null}
                  </>
                ) : (
                  "Loading…"
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="text-sm font-semibold">Actions</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {!status?.is_installed ? (
              <button
                type="button"
                onClick={() => void handleInstall()}
                disabled={isInstalling}
                className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isInstalling ? "Installing…" : "Install ComfyUI"}
              </button>
            ) : null}
            {canStart ? (
              <button
                type="button"
                onClick={() => void handleStart()}
                disabled={isStarting}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isStarting ? "Starting…" : "Start"}
              </button>
            ) : null}
            {canStop ? (
              <button
                type="button"
                onClick={() => void handleStop()}
                disabled={isStopping}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isStopping ? "Stopping…" : "Stop"}
              </button>
            ) : null}
            {canRestart ? (
              <button
                type="button"
                onClick={() => void handleRestart()}
                disabled={isRestarting}
                className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isRestarting ? "Restarting…" : "Restart"}
              </button>
            ) : null}
            {status?.is_installed ? (
              <button
                type="button"
                onClick={() => void handleSyncModels()}
                disabled={isSyncing}
                className="rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSyncing ? "Syncing…" : "Sync Models"}
              </button>
            ) : null}
          </div>
        </div>

        <div className="mt-6 rounded-xl border border-zinc-200 bg-white p-5">
          <div className="flex items-center justify-between gap-4">
            <div className="text-sm font-semibold">Logs</div>
            <div className="text-xs text-zinc-500">{logs.length} entries</div>
          </div>
          <div className="mt-3 max-h-[400px] overflow-y-auto rounded-lg border border-zinc-200 bg-zinc-50 p-3 font-mono text-xs">
            {logs.length === 0 ? (
              <div className="text-zinc-500">(no logs yet)</div>
            ) : (
              logs.map((log, idx) => {
                // Parse log string: "[YYYY-MM-DD HH:MM:SS] [LEVEL] message"
                const match = log.match(/^\[([^\]]+)\] \[([^\]]+)\] (.+)$/);
                const timestamp = match ? match[1] : "";
                const level = match ? match[2] : "";
                const message = match ? match[3] : log;
                const isError = level === "ERROR" || level === "error";
                const isWarning = level === "WARNING" || level === "warning";
                return (
                  <div key={idx} className="mb-1 break-words">
                    <span className="text-zinc-500">{timestamp}</span>
                    <span
                      className={
                        isError ? "ml-2 text-red-700" : isWarning ? "ml-2 text-amber-700" : "ml-2 text-zinc-700"
                      }
                    >
                      [{level}] {message}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

