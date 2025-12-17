"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { DashboardHeader } from "@/components/DashboardHeader";

type Character = {
  id: string;
  name: string;
  bio: string | null;
  status: string;
  profile_image_url: string | null;
  created_at: string;
};

type CharactersResponse = {
  success: boolean;
  data: {
    characters: Character[];
    total: number;
    limit: number;
    offset: number;
  };
};

type AnalyticsOverview = {
  success: boolean;
  data: {
    total_posts: number;
    total_engagement: number;
    total_followers: number;
    engagement_rate: number;
    follower_growth: number;
  };
};

type UnifiedStatus = {
  overall_status: "ok" | "warning" | "error";
  backend: {
    status: string;
    message: string;
    state: "unknown" | "running" | "stopped" | "error";
    port: number;
    host: string;
    process_id: number | null;
    last_check: number | null;
  };
  frontend: {
    status: string;
    message: string;
    state: "unknown" | "running" | "stopped" | "error";
    port: number;
    host: string;
    process_id: number | null;
    last_check: number | null;
  };
  comfyui_manager: {
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
  comfyui_service: {
    state: "unknown" | "running" | "stopped" | "error";
    port: number;
    host: string;
    process_id: number | null;
    message: string | null;
    error: string | null;
    last_check: number | null;
    installed: boolean;
    base_url: string | null;
    reachable: boolean;
    stats: unknown;
  };
  system: {
    ts: number;
    os: {
      system: string;
      release: string;
      version: string;
      machine: string;
    };
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
    issues: Array<{
      code: string;
      severity: "error" | "warn";
      title: string;
      detail: string;
    }>;
  };
};

type ErrorAggregation = {
  by_level: Record<string, number>;
  by_source: Record<string, number>;
  total: number;
  recent_count: number;
};

type ErrorEntry = {
  timestamp: string;
  level: string;
  source: string;
  message: string;
  details?: Record<string, unknown>;
};

type LogEntry = {
  timestamp: number;
  level: string;
  source: string;
  message: string;
  raw: unknown;
};

type LogsResponse = {
  logs: LogEntry[];
  count: number;
  sources: string[];
  levels: string[];
};

function StatusBadge({ status }: { status: "ok" | "warning" | "error" }) {
  const colors = {
    ok: "bg-green-100 text-green-800 border-green-200",
    warning: "bg-yellow-100 text-yellow-800 border-yellow-200",
    error: "bg-red-100 text-red-800 border-red-200",
  };
  const labels = {
    ok: "Healthy",
    warning: "Warning",
    error: "Error",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${colors[status]}`}
    >
      {labels[status]}
    </span>
  );
}

function ServiceCard({
  title,
  status,
  details,
  icon,
  port,
  processId,
  health,
}: {
  title: string;
  status: "ok" | "warning" | "error";
  details: string | null;
  icon?: string;
  port?: number | null;
  processId?: number | null;
  health?: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {icon && <span className="text-xl">{icon}</span>}
          <div className="flex-1">
            <div className="text-sm font-semibold">{title}</div>
            {details && <div className="mt-1 text-xs text-zinc-600">{details}</div>}
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-zinc-500">
              {port && <span>Port: {port}</span>}
              {processId && <span>PID: {processId}</span>}
              {health && <span>Health: {health}</span>}
            </div>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>
    </div>
  );
}

export default function Home() {
  const [status, setStatus] = useState<UnifiedStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorAggregation, setErrorAggregation] = useState<ErrorAggregation | null>(null);
  const [recentErrors, setRecentErrors] = useState<ErrorEntry[]>([]);
  const [errorsLoading, setErrorsLoading] = useState(true);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(true);
  const [logsFilter, setLogsFilter] = useState<{ source: string | null; level: string | null }>({
    source: null,
    level: null,
  });
  const [logsMeta, setLogsMeta] = useState<{ sources: string[]; levels: string[] } | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [charactersLoading, setCharactersLoading] = useState(true);
  const [analytics, setAnalytics] = useState<AnalyticsOverview["data"] | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);

  async function loadStatus() {
    try {
      setError(null);
      const data = await apiGet<UnifiedStatus>("/api/status");
      setStatus(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function loadErrors() {
    try {
      const [aggregation, errorsData] = await Promise.all([
        apiGet<ErrorAggregation>("/api/errors/aggregation"),
        apiGet<{ errors: ErrorEntry[]; aggregation: ErrorAggregation; count: number }>("/api/errors?limit=10"),
      ]);
      setErrorAggregation(aggregation);
      setRecentErrors(errorsData.errors);
    } catch (e) {
      // Silently fail - errors endpoint might not be critical
      console.error("Failed to load errors:", e);
    } finally {
      setErrorsLoading(false);
    }
  }

  async function loadLogs() {
    try {
      const params = new URLSearchParams();
      params.append("limit", "100");
      if (logsFilter.source) {
        params.append("source", logsFilter.source);
      }
      if (logsFilter.level) {
        params.append("level", logsFilter.level);
      }
      const data = await apiGet<LogsResponse>(`/api/logs?${params.toString()}`);
      setLogs(data.logs);
      setLogsMeta({ sources: data.sources, levels: data.levels });
    } catch (e) {
      console.error("Failed to load logs:", e);
    } finally {
      setLogsLoading(false);
    }
  }

  async function loadCharacters() {
    try {
      const response = await apiGet<CharactersResponse>("/api/characters?limit=12&offset=0");
      if (response.success) {
        setCharacters(response.data.characters);
      }
    } catch (e) {
      console.error("Failed to load characters:", e);
    } finally {
      setCharactersLoading(false);
    }
  }

  async function loadAnalytics() {
    try {
      const response = await apiGet<AnalyticsOverview>("/api/analytics/overview");
      if (response.success) {
        setAnalytics(response.data);
      }
    } catch (e) {
      console.error("Failed to load analytics:", e);
    } finally {
      setAnalyticsLoading(false);
    }
  }

  useEffect(() => {
    // Real-time monitoring via WebSocket
    const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    const wsUrl = apiUrl.replace(/^http/, "ws") + "/api/ws/monitoring";
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000;

    function connectWebSocket() {
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log("WebSocket connected for real-time monitoring");
          reconnectAttempts = 0;
          // Load initial status via REST (fallback)
          loadStatus();
        };

        ws.onmessage = (event) => {
          try {
            // Handle ping/pong
            if (event.data === "ping") {
              ws?.send("pong");
              return;
            }
            if (event.data === "pong") {
              return;
            }
            
            // Parse status update
            const data = JSON.parse(event.data) as UnifiedStatus;
            setStatus(data);
            setLoading(false);
            setError(null);
          } catch (e) {
            console.error("Failed to parse WebSocket message:", e);
          }
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          setError("WebSocket connection error. Falling back to polling.");
        };

        ws.onclose = () => {
          console.log("WebSocket disconnected");
          ws = null;
          
          // Attempt to reconnect
          if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            reconnectTimeout = setTimeout(() => {
              console.log(`Reconnecting WebSocket (attempt ${reconnectAttempts})...`);
              connectWebSocket();
            }, reconnectDelay);
          } else {
            // Fall back to polling after max attempts
            console.log("Max reconnect attempts reached. Falling back to polling.");
            const statusInterval = setInterval(loadStatus, 5000);
            return () => clearInterval(statusInterval);
          }
        };
      } catch (e) {
        console.error("Failed to create WebSocket:", e);
        setError("WebSocket not available. Falling back to polling.");
        // Fall back to polling
        const statusInterval = setInterval(loadStatus, 5000);
        return () => clearInterval(statusInterval);
      }
    }

    // Initial load and WebSocket connection
    loadStatus();
    loadErrors();
    loadLogs();
    loadCharacters();
    loadAnalytics();
    connectWebSocket();

    // Polling for errors and logs (can be upgraded to WebSocket later)
    const errorsInterval = setInterval(loadErrors, 5000);
    const logsInterval = setInterval(loadLogs, 5000);
    
    // Keyboard shortcuts
    const handleKeyPress = (e: KeyboardEvent) => {
      // Cmd/Ctrl + R: Refresh all
      if ((e.metaKey || e.ctrlKey) && e.key === "r") {
        e.preventDefault();
        loadStatus();
        loadErrors();
        loadLogs();
      }
      // Cmd/Ctrl + L: Jump to logs
      if ((e.metaKey || e.ctrlKey) && e.key === "l") {
        e.preventDefault();
        const logsSection = document.getElementById("logs-section");
        logsSection?.scrollIntoView({ behavior: "smooth" });
      }
    };
    
    window.addEventListener("keydown", handleKeyPress);
    
    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      clearInterval(errorsInterval);
      clearInterval(logsInterval);
      window.removeEventListener("keydown", handleKeyPress);
    };
  }, []);

  useEffect(() => {
    loadLogs();
  }, [logsFilter]);

  function getServiceStatus(serviceName: string): "ok" | "warning" | "error" {
    if (!status) return "warning";
    if (serviceName === "backend") {
      if (status.backend.state === "running") return "ok";
      if (status.backend.state === "error") return "error";
      return "warning";
    }
    if (serviceName === "frontend") {
      if (status.frontend.state === "running") return "ok";
      if (status.frontend.state === "error") return "error";
      return "warning";
    }
    if (serviceName === "comfyui") {
      if (status.comfyui_service.state === "running" && status.comfyui_service.reachable) {
        return "ok";
      }
      if (status.comfyui_service.state === "error" || status.comfyui_manager.state === "error") {
        return "error";
      }
      if (status.comfyui_service.state === "stopped" && !status.comfyui_service.installed) {
        return "warning";
      }
      return "warning";
    }
    return "warning";
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500/20 text-green-700 border-green-500/30";
      case "paused":
        return "bg-yellow-500/20 text-yellow-700 border-yellow-500/30";
      case "error":
        return "bg-red-500/20 text-red-700 border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-700 border-gray-500/30";
    }
  };

  const activeCharacters = characters.filter((c) => c.status === "active").length;
  const totalCharacters = characters.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 via-white to-zinc-50 text-zinc-900">
      <main className="mx-auto w-full max-w-7xl px-4 sm:px-6 py-8 sm:py-12">
        {/* Header */}
        <DashboardHeader />

        {/* Stats Cards */}
        <div className="mb-8 grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-zinc-600">Total Characters</div>
                <div className="mt-2 text-3xl font-bold text-zinc-900">
                  {charactersLoading ? "..." : totalCharacters}
                </div>
                <div className="mt-1 text-xs text-zinc-500">
                  {activeCharacters} active
                </div>
              </div>
              <div className="rounded-lg bg-indigo-100 p-3">
                <span className="text-2xl">👤</span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-zinc-600">Total Posts</div>
                <div className="mt-2 text-3xl font-bold text-zinc-900">
                  {analyticsLoading ? "..." : analytics?.total_posts.toLocaleString() || "0"}
                </div>
                <div className="mt-1 text-xs text-zinc-500">All time</div>
              </div>
              <div className="rounded-lg bg-purple-100 p-3">
                <span className="text-2xl">📊</span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-zinc-600">Total Engagement</div>
                <div className="mt-2 text-3xl font-bold text-zinc-900">
                  {analyticsLoading ? "..." : analytics?.total_engagement.toLocaleString() || "0"}
                </div>
                <div className="mt-1 text-xs text-zinc-500">
                  {analytics?.engagement_rate ? `${(analytics.engagement_rate * 100).toFixed(1)}% rate` : "—"}
                </div>
              </div>
              <div className="rounded-lg bg-green-100 p-3">
                <span className="text-2xl">❤️</span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-zinc-600">System Health</div>
                <div className="mt-2">
                  {status ? (
                    <StatusBadge status={status.overall_status} />
                  ) : (
                    <span className="text-3xl font-bold text-zinc-400">—</span>
                  )}
                </div>
                <div className="mt-1 text-xs text-zinc-500">
                  {status?.overall_status === "ok" ? "All systems operational" : "Check status"}
                </div>
              </div>
              <div className="rounded-lg bg-blue-100 p-3">
                <span className="text-2xl">⚡</span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Status Banner */}
        {status && status.overall_status !== "ok" && (
          <div className={`mb-6 rounded-xl border p-4 ${
            status.overall_status === "warning"
              ? "border-yellow-200 bg-yellow-50"
              : "border-red-200 bg-red-50"
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <StatusBadge status={status.overall_status} />
                <div className="text-sm">
                  {status.overall_status === "warning" && "Some services need attention"}
                  {status.overall_status === "error" && "System errors detected"}
                </div>
              </div>
              <button
                onClick={() => {
                  const logsSection = document.getElementById("logs-section");
                  logsSection?.scrollIntoView({ behavior: "smooth" });
                }}
                className="text-xs font-medium text-zinc-700 hover:text-zinc-900 underline"
              >
                View logs ↓
              </button>
            </div>
          </div>
        )}

        {/* Characters Grid */}
        <div className="mb-8 sm:mb-10">
          <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-zinc-900">Characters</h2>
              <p className="mt-1 text-xs sm:text-sm text-zinc-600">Manage your AI influencer characters</p>
            </div>
            <Link
              href="/characters"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-700 self-start sm:self-auto"
            >
              View all →
            </Link>
          </div>

          {charactersLoading ? (
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="rounded-xl border border-zinc-200 bg-white p-5 animate-pulse">
                  <div className="h-32 bg-zinc-200 rounded-lg mb-3"></div>
                  <div className="h-4 bg-zinc-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-zinc-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : characters.length > 0 ? (
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {characters.slice(0, 8).map((character) => (
                <Link
                  key={character.id}
                  href={`/characters/${character.id}`}
                  className="group rounded-xl border border-zinc-200 bg-white p-5 hover:border-indigo-300 hover:shadow-lg transition-all"
                >
                  <div className="mb-3 flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-zinc-900 group-hover:text-indigo-600 transition-colors">
                        {character.name}
                      </h3>
                      {character.bio && (
                        <p className="mt-1 text-xs text-zinc-600 line-clamp-2">{character.bio}</p>
                      )}
                    </div>
                    {character.profile_image_url ? (
                      <img
                        src={character.profile_image_url}
                        alt={character.name}
                        className="w-12 h-12 rounded-lg object-cover ml-3"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-indigo-400 to-purple-400 ml-3 flex items-center justify-center text-white font-semibold">
                        {character.name.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span
                      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${getStatusColor(character.status)}`}
                    >
                      {character.status}
                    </span>
                    <span className="text-xs text-zinc-500">
                      {new Date(character.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center">
              <div className="text-4xl mb-4">👤</div>
              <h3 className="text-lg font-semibold text-zinc-900 mb-2">No characters yet</h3>
              <p className="text-sm text-zinc-600 mb-4">Create your first AI influencer character to get started.</p>
              <Link
                href="/characters/create"
                className="inline-block rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
              >
                Create Character
              </Link>
            </div>
          )}
        </div>

        {/* System Status Dashboard */}
        <div className="mb-8 sm:mb-10">
          <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-zinc-900">System Status</h2>
              <p className="mt-1 text-xs sm:text-sm text-zinc-600">Monitor service health and system resources</p>
            </div>
            {status && (
              <div className="flex items-center gap-2 self-start sm:self-auto">
                <StatusBadge status={status.overall_status} />
                <button
                  onClick={loadStatus}
                  className="text-xs text-zinc-600 hover:text-zinc-900"
                  disabled={loading}
                >
                  {loading ? "Refreshing..." : "Refresh"}
                </button>
              </div>
            )}
          </div>

          {loading && !status && (
            <div className="rounded-xl border border-zinc-200 bg-white p-8">
              <div className="flex items-center justify-center gap-3">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900"></div>
                <span className="text-sm text-zinc-600">Loading system status...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="text-sm font-semibold text-red-900">Error loading status</div>
                  <div className="mt-1 text-sm text-red-800">{error}</div>
                </div>
                <button
                  onClick={loadStatus}
                  className="shrink-0 rounded border border-red-300 bg-white px-3 py-1.5 text-xs font-medium text-red-800 hover:bg-red-100"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {status && (
            <>
              {/* Service Status Cards */}
              <div className="mb-6 grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                {loading && !status ? (
                  <>
                    <div className="rounded-xl border border-zinc-200 bg-white p-5 animate-pulse">
                      <div className="h-4 w-24 bg-zinc-200 rounded mb-2"></div>
                      <div className="h-3 w-32 bg-zinc-200 rounded"></div>
                    </div>
                    <div className="rounded-xl border border-zinc-200 bg-white p-5 animate-pulse">
                      <div className="h-4 w-24 bg-zinc-200 rounded mb-2"></div>
                      <div className="h-3 w-32 bg-zinc-200 rounded"></div>
                    </div>
                    <div className="rounded-xl border border-zinc-200 bg-white p-5 animate-pulse">
                      <div className="h-4 w-24 bg-zinc-200 rounded mb-2"></div>
                      <div className="h-3 w-32 bg-zinc-200 rounded"></div>
                    </div>
                  </>
                ) : (
                  <>
                    <ServiceCard
                      title="Backend"
                      status={getServiceStatus("backend")}
                      details={status.backend.message}
                      icon="⚙️"
                      port={status.backend.port}
                      processId={status.backend.process_id}
                      health={status.backend.state}
                    />
                    <ServiceCard
                      title="Frontend"
                      status={getServiceStatus("frontend")}
                      details={status.frontend.message}
                      icon="🖥️"
                      port={status.frontend.port}
                      processId={status.frontend.process_id}
                      health={status.frontend.state}
                    />
                    <ServiceCard
                      title="ComfyUI"
                      status={getServiceStatus("comfyui")}
                      details={
                        status.comfyui_service.message ||
                        status.comfyui_manager.message ||
                        `State: ${status.comfyui_service.state}`
                      }
                      icon="🎨"
                      port={status.comfyui_service.port}
                      processId={status.comfyui_service.process_id}
                      health={status.comfyui_service.state}
                    />
                  </>
                )}
              </div>

              {/* System Information */}
              <div className="mb-6 grid gap-4 grid-cols-2 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border border-zinc-200 bg-white p-4">
                  <div className="text-xs font-medium text-zinc-600">OS</div>
                  <div className="mt-1 text-sm font-semibold">
                    {status.system.os.system} {status.system.os.release}
                  </div>
                </div>
                <div className="rounded-xl border border-zinc-200 bg-white p-4">
                  <div className="text-xs font-medium text-zinc-600">Python</div>
                  <div className="mt-1 text-sm font-semibold">
                    {status.system.python.version}
                    {status.system.python.supported ? " ✓" : " ✗"}
                  </div>
                </div>
                <div className="rounded-xl border border-zinc-200 bg-white p-4">
                  <div className="text-xs font-medium text-zinc-600">Disk Space</div>
                  <div className="mt-1 text-sm font-semibold">
                    {status.system.resources.disk_free_gb.toFixed(1)} GB free
                  </div>
                </div>
                <div className="rounded-xl border border-zinc-200 bg-white p-4">
                  <div className="text-xs font-medium text-zinc-600">GPU</div>
                  <div className="mt-1 text-sm font-semibold">
                    {status.system.gpu.nvidia_smi ? "NVIDIA ✓" : "Not detected"}
                  </div>
                </div>
              </div>

              {/* Issues */}
              {status.system.issues.length > 0 && (
                <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-4">
                  <div className="mb-2 text-sm font-semibold text-yellow-900">System Issues</div>
                  <ul className="space-y-1">
                    {status.system.issues.map((issue, idx) => (
                      <li key={idx} className="text-xs text-yellow-800">
                        <strong>{issue.title}:</strong> {issue.detail}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>

        {/* Error Aggregation Panel */}
        <div className="mb-8 sm:mb-10">
          <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-zinc-900">Error Log</h2>
              <p className="mt-1 text-xs sm:text-sm text-zinc-600">Track and monitor system errors</p>
            </div>
            {errorAggregation && (
              <button
                onClick={loadErrors}
                className="text-xs text-zinc-600 hover:text-zinc-900 self-start sm:self-auto"
                disabled={errorsLoading}
              >
                {errorsLoading ? "Refreshing..." : "Refresh"}
              </button>
            )}
          </div>

          {errorsLoading && !errorAggregation && (
            <div className="rounded-xl border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-600">
              Loading error log...
            </div>
          )}

          {errorAggregation && (
            <>
              {/* Error Aggregation Stats */}
              <div className="mb-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border border-zinc-200 bg-white p-4">
                  <div className="text-xs font-medium text-zinc-600">Total Errors</div>
                  <div className="mt-1 text-lg font-semibold">{errorAggregation.total}</div>
                </div>
                <div className="rounded-xl border border-zinc-200 bg-white p-4">
                  <div className="text-xs font-medium text-zinc-600">Last 24h</div>
                  <div className="mt-1 text-lg font-semibold">{errorAggregation.recent_count}</div>
                </div>
                <div className="rounded-xl border border-zinc-200 bg-white p-4">
                  <div className="text-xs font-medium text-zinc-600">By Level</div>
                  <div className="mt-1 space-y-1">
                    {Object.entries(errorAggregation.by_level).map(([level, count]) => (
                      <div key={level} className="text-sm">
                        <span className="font-medium capitalize">{level}:</span>{" "}
                        <span className="text-zinc-600">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="rounded-xl border border-zinc-200 bg-white p-4">
                  <div className="text-xs font-medium text-zinc-600">By Source</div>
                  <div className="mt-1 space-y-1">
                    {Object.entries(errorAggregation.by_source).map(([source, count]) => (
                      <div key={source} className="text-sm">
                        <span className="font-medium capitalize">{source}:</span>{" "}
                        <span className="text-zinc-600">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recent Errors List */}
              {recentErrors.length > 0 && (
                <div className="rounded-xl border border-zinc-200 bg-white p-4">
                  <div className="mb-3 text-sm font-semibold">Recent Errors</div>
                  <div className="space-y-2">
                    {recentErrors.map((err, idx) => (
                      <div
                        key={idx}
                        className="rounded border border-zinc-100 bg-zinc-50 p-3 text-xs"
                      >
                        <div className="mb-1 flex items-center justify-between">
                          <span
                            className={`rounded px-2 py-0.5 font-medium ${
                              err.level === "error"
                                ? "bg-red-100 text-red-800"
                                : err.level === "warning"
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-blue-100 text-blue-800"
                            }`}
                          >
                            {err.level.toUpperCase()}
                          </span>
                          <span className="text-zinc-500">
                            {new Date(err.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <div className="mb-1">
                          <span className="font-medium text-zinc-700">Source:</span>{" "}
                          <span className="text-zinc-600">{err.source}</span>
                        </div>
                        <div className="text-zinc-700">{err.message}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {recentErrors.length === 0 && errorAggregation.total === 0 && (
                <div className="rounded-xl border border-green-200 bg-green-50 p-4 text-center text-sm text-green-800">
                  ✓ No errors logged
                </div>
              )}
            </>
          )}
        </div>

        {/* Logs Viewer Panel */}
        <div id="logs-section" className="mb-8 sm:mb-10">
          <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-zinc-900">System Logs</h2>
              <p className="mt-1 text-xs sm:text-sm text-zinc-600">Real-time system activity and events</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {logsMeta && (
                <>
                  <select
                    value={logsFilter.source || ""}
                    onChange={(e) => setLogsFilter({ ...logsFilter, source: e.target.value || null })}
                    className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs"
                  >
                    <option value="">All Sources</option>
                    {logsMeta.sources.map((src) => (
                      <option key={src} value={src}>
                        {src}
                      </option>
                    ))}
                  </select>
                  <select
                    value={logsFilter.level || ""}
                    onChange={(e) => setLogsFilter({ ...logsFilter, level: e.target.value || null })}
                    className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs"
                  >
                    <option value="">All Levels</option>
                    {logsMeta.levels.map((lvl) => (
                      <option key={lvl} value={lvl}>
                        {lvl.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </>
              )}
              {logs.length > 0 && (
                <button
                  onClick={async () => {
                    const logText = logs.map((log) => {
                      const timestamp = new Date(log.timestamp * 1000).toLocaleString();
                      return `${timestamp} [${log.level.toUpperCase()}] [${log.source}] ${log.message}`;
                    }).join("\n");
                    try {
                      await navigator.clipboard.writeText(logText);
                      // Show brief success feedback
                      const btn = event?.target as HTMLButtonElement;
                      const originalText = btn.textContent;
                      btn.textContent = "Copied!";
                      setTimeout(() => {
                        btn.textContent = originalText;
                      }, 2000);
                    } catch (err) {
                      console.error("Failed to copy logs:", err);
                    }
                  }}
                  className="text-xs text-zinc-600 hover:text-zinc-900"
                  title="Copy logs to clipboard"
                >
                  Copy
                </button>
              )}
              <button
                onClick={loadLogs}
                className="text-xs text-zinc-600 hover:text-zinc-900"
                disabled={logsLoading}
              >
                {logsLoading ? "Refreshing..." : "Refresh"}
              </button>
            </div>
          </div>

          {logsLoading && logs.length === 0 && (
            <div className="rounded-xl border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-600">
              Loading logs...
            </div>
          )}

          {logs.length > 0 && (
            <div className="max-h-[500px] overflow-auto rounded-xl border border-zinc-200 bg-black p-4">
              <div className="space-y-1 font-mono text-xs">
                {logs.map((log, idx) => {
                  const isError = log.level === "error";
                  const isWarning = log.level === "warning";
                  const timestamp = new Date(log.timestamp * 1000).toLocaleString();
                  return (
                    <div key={idx} className="break-words leading-5 hover:bg-zinc-900/50 px-2 py-1 rounded transition-colors">
                      <span className="text-zinc-500">{timestamp}</span>
                      <span
                        className={`ml-2 ${
                          isError
                            ? "text-red-400"
                            : isWarning
                              ? "text-yellow-400"
                              : "text-zinc-300"
                        }`}
                      >
                        [{log.level.toUpperCase()}] [{log.source}]
                      </span>
                      <span className="ml-2 text-zinc-100">{log.message}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {logs.length === 0 && !logsLoading && (
            <div className="rounded-xl border border-zinc-200 bg-white p-4 text-center text-sm text-zinc-600">
              No logs available
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mb-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-zinc-900">Quick Actions</h2>
              <p className="mt-1 text-sm text-zinc-600">Access key features and tools</p>
            </div>
            <div className="text-xs text-zinc-500">
              <kbd className="rounded border border-zinc-300 bg-zinc-100 px-1.5 py-0.5 font-mono">⌘R</kbd> Refresh • <kbd className="rounded border border-zinc-300 bg-zinc-100 px-1.5 py-0.5 font-mono">⌘L</kbd> Logs
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Link
              href="/characters"
              className="group rounded-xl border border-zinc-200 bg-white p-5 hover:border-indigo-300 hover:shadow-md transition-all"
            >
              <div className="text-2xl mb-2">👤</div>
              <div className="text-sm font-semibold text-zinc-900 group-hover:text-indigo-600 transition-colors">Characters</div>
              <div className="mt-2 text-xs text-zinc-600">
                Manage AI influencer characters
              </div>
            </Link>

            <Link
              href="/generate"
              className="group rounded-xl border border-zinc-200 bg-white p-5 hover:border-indigo-300 hover:shadow-md transition-all"
            >
              <div className="text-2xl mb-2">🎨</div>
              <div className="text-sm font-semibold text-zinc-900 group-hover:text-indigo-600 transition-colors">Generate</div>
              <div className="mt-2 text-xs text-zinc-600">
                Create images with ComfyUI
              </div>
            </Link>

            <Link
              href="/models"
              className="group rounded-xl border border-zinc-200 bg-white p-5 hover:border-indigo-300 hover:shadow-md transition-all"
            >
              <div className="text-2xl mb-2">📦</div>
              <div className="text-sm font-semibold text-zinc-900 group-hover:text-indigo-600 transition-colors">Models</div>
              <div className="mt-2 text-xs text-zinc-600">
                Browse and manage AI models
              </div>
            </Link>

            <Link
              href="/analytics"
              className="group rounded-xl border border-zinc-200 bg-white p-5 hover:border-indigo-300 hover:shadow-md transition-all"
            >
              <div className="text-2xl mb-2">📊</div>
              <div className="text-sm font-semibold text-zinc-900 group-hover:text-indigo-600 transition-colors">Analytics</div>
              <div className="mt-2 text-xs text-zinc-600">
                View performance metrics
              </div>
            </Link>

            <Link
              href="/installer"
              className="group rounded-xl border border-zinc-200 bg-white p-5 hover:border-indigo-300 hover:shadow-md transition-all"
            >
              <div className="text-2xl mb-2">⚙️</div>
              <div className="text-sm font-semibold text-zinc-900 group-hover:text-indigo-600 transition-colors">Settings</div>
              <div className="mt-2 text-xs text-zinc-600">
                System setup and configuration
              </div>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
