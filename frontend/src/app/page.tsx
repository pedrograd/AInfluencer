"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import {
  MetricCard,
  StatusChip,
  SectionCard,
  PageHeader,
  EmptyState,
  LoadingSkeleton,
  Alert,
  ErrorBanner,
  PrimaryButton,
  SecondaryButton,
  IconButton,
} from "@/components/ui";
import {
  Users,
  FileText,
  Heart,
  Activity,
  Settings,
  Sparkles,
  Package,
  BarChart3,
  Wrench,
  RefreshCw,
  Copy,
  ChevronRight,
} from "lucide-react";

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
  icon?: React.ReactNode;
  port?: number | null;
  processId?: number | null;
  health?: string;
}) {
  return (
    <SectionCard variant="elevated">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1">
          {icon && <div className="text-[var(--text-muted)]">{icon}</div>}
          <div className="flex-1">
            <div className="text-sm font-semibold text-[var(--text-primary)]">
              {title}
            </div>
            {details && (
              <div className="mt-1 text-xs text-[var(--text-secondary)]">
                {details}
              </div>
            )}
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-[var(--text-muted)]">
              {port && <span>Port: {port}</span>}
              {processId && <span>PID: {processId}</span>}
              {health && <span>Health: {health}</span>}
            </div>
          </div>
        </div>
        <StatusChip status={status === "ok" ? "success" : status} />
      </div>
    </SectionCard>
  );
}

export default function Home() {
  const router = useRouter();
  const [status, setStatus] = useState<UnifiedStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [setupChecked, setSetupChecked] = useState(false);
  const [errorAggregation, setErrorAggregation] =
    useState<ErrorAggregation | null>(null);
  const [recentErrors, setRecentErrors] = useState<ErrorEntry[]>([]);
  const [errorsLoading, setErrorsLoading] = useState(true);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(true);
  const [logsFilter, setLogsFilter] = useState<{
    source: string | null;
    level: string | null;
  }>({
    source: null,
    level: null,
  });
  const [logsMeta, setLogsMeta] = useState<{
    sources: string[];
    levels: string[];
  } | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [charactersLoading, setCharactersLoading] = useState(true);
  const [analytics, setAnalytics] = useState<AnalyticsOverview["data"] | null>(
    null
  );
  const [analyticsLoading, setAnalyticsLoading] = useState(true);

  // Check if system is set up on first load
  useEffect(() => {
    async function checkSetup() {
      try {
        const installerStatus = await apiGet<{ state: string }>(
          "/api/installer/status"
        );
        if (installerStatus.state !== "succeeded") {
          router.push("/installer");
          return;
        }
        setSetupChecked(true);
      } catch (e) {
        console.error("Failed to check setup status:", e);
        router.push("/installer");
      }
    }
    if (!setupChecked) {
      void checkSetup();
    }
  }, [router, setupChecked]);

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
        apiGet<{
          errors: ErrorEntry[];
          aggregation: ErrorAggregation;
          count: number;
        }>("/api/errors?limit=10"),
      ]);
      setErrorAggregation(aggregation);
      setRecentErrors(errorsData.errors);
    } catch (e) {
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
      const response = await apiGet<CharactersResponse>(
        "/api/characters?limit=12&offset=0"
      );
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
      const response = await apiGet<AnalyticsOverview>(
        "/api/analytics/overview"
      );
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
    if (!setupChecked) {
      return;
    }

    const apiUrl =
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
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
          loadStatus();
        };

        ws.onmessage = (event) => {
          try {
            if (event.data === "ping") {
              ws?.send("pong");
              return;
            }
            if (event.data === "pong") {
              return;
            }

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

          if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            reconnectTimeout = setTimeout(() => {
              console.log(
                `Reconnecting WebSocket (attempt ${reconnectAttempts})...`
              );
              connectWebSocket();
            }, reconnectDelay);
          } else {
            console.log(
              "Max reconnect attempts reached. Falling back to polling."
            );
            const statusInterval = setInterval(loadStatus, 5000);
            return () => clearInterval(statusInterval);
          }
        };
      } catch (e) {
        console.error("Failed to create WebSocket:", e);
        setError("WebSocket not available. Falling back to polling.");
        const statusInterval = setInterval(loadStatus, 5000);
        return () => clearInterval(statusInterval);
      }
    }

    loadStatus();
    loadErrors();
    loadLogs();
    loadCharacters();
    loadAnalytics();
    connectWebSocket();

    const errorsInterval = setInterval(loadErrors, 5000);
    const logsInterval = setInterval(loadLogs, 5000);

    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "r") {
        e.preventDefault();
        loadStatus();
        loadErrors();
        loadLogs();
      }
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
  }, [setupChecked]);

  useEffect(() => {
    loadLogs();
  }, [logsFilter]);

  if (!setupChecked) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)] flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-medium text-[var(--text-primary)]">
            Checking setup...
          </div>
          <div className="mt-2 text-sm text-[var(--text-secondary)]">
            Redirecting to Setup if needed
          </div>
        </div>
      </div>
    );
  }

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
      if (
        status.comfyui_service.state === "running" &&
        status.comfyui_service.reachable
      ) {
        return "ok";
      }
      if (
        status.comfyui_service.state === "error" ||
        status.comfyui_manager.state === "error"
      ) {
        return "error";
      }
      if (
        status.comfyui_service.state === "stopped" &&
        !status.comfyui_service.installed
      ) {
        return "warning";
      }
      return "warning";
    }
    return "warning";
  }

  const activeCharacters = characters.filter(
    (c) => c.status === "active"
  ).length;
  const totalCharacters = characters.length;

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        {/* Header */}
        <PageHeader
          title="Dashboard"
          description="System health overview and quick actions"
        />

        {/* Stats Cards */}
        <div className="mb-8 grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            label="Total Characters"
            value={charactersLoading ? "..." : totalCharacters}
            trend={
              totalCharacters > 0
                ? {
                    value: activeCharacters,
                    label: `${activeCharacters} active`,
                  }
                : undefined
            }
            icon={<Users className="h-5 w-5" />}
            variant="icon"
          />
          <MetricCard
            label="Total Posts"
            value={
              analyticsLoading
                ? "..."
                : analytics?.total_posts.toLocaleString() || "0"
            }
            trend={
              analytics?.engagement_rate
                ? {
                    value: analytics.engagement_rate * 100,
                    label: `${(analytics.engagement_rate * 100).toFixed(
                      1
                    )}% engagement`,
                  }
                : undefined
            }
            icon={<FileText className="h-5 w-5" />}
            variant="icon"
          />
          <MetricCard
            label="Total Engagement"
            value={
              analyticsLoading
                ? "..."
                : analytics?.total_engagement.toLocaleString() || "0"
            }
            icon={<Heart className="h-5 w-5" />}
            variant="icon"
          />
          <MetricCard
            label="System Health"
            value={
              status ? (
                <StatusChip
                  status={
                    status.overall_status === "ok"
                      ? "success"
                      : status.overall_status
                  }
                />
              ) : (
                <span className="text-[var(--text-muted)]">—</span>
              )
            }
            icon={<Activity className="h-5 w-5" />}
            variant="icon"
          />
        </div>

        {/* Status Banner */}
        {status && status.overall_status !== "ok" && (
          <div className="mb-6">
            <Alert
              message={
                status.overall_status === "warning"
                  ? "Some services need attention"
                  : "System errors detected"
              }
              variant={status.overall_status === "error" ? "error" : "warning"}
              action={{
                label: "View logs",
                onClick: () => {
                  const logsSection = document.getElementById("logs-section");
                  logsSection?.scrollIntoView({ behavior: "smooth" });
                },
              }}
            />
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="mb-6">
            <ErrorBanner
              title="Error loading status"
              message={error}
              remediation={{
                label: "Retry",
                onClick: loadStatus,
              }}
            />
          </div>
        )}

        {/* Characters Grid */}
        <SectionCard
          title="Recent Characters"
          description="Manage your AI influencer characters"
          action={
            <Link href="/characters">
              <SecondaryButton
                size="sm"
                icon={<ChevronRight className="h-4 w-4" />}
              >
                View all
              </SecondaryButton>
            </Link>
          }
          loading={charactersLoading}
          empty={!charactersLoading && characters.length === 0}
          emptyMessage="No characters yet"
          className="mb-8"
        >
          {charactersLoading ? (
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <LoadingSkeleton key={i} variant="card" height="200px" />
              ))}
            </div>
          ) : characters.length > 0 ? (
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {characters.slice(0, 8).map((character) => (
                <Link
                  key={character.id}
                  href={`/characters/${character.id}`}
                  className="group rounded-xl border border-[var(--border-base)] bg-[var(--bg-elevated)] p-5 hover:border-[var(--accent-primary)] hover:shadow-lg transition-all"
                >
                  <div className="mb-3 flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-primary)] transition-colors">
                        {character.name}
                      </h3>
                      {character.bio && (
                        <p className="mt-1 text-xs text-[var(--text-secondary)] line-clamp-2">
                          {character.bio}
                        </p>
                      )}
                    </div>
                    {character.profile_image_url ? (
                      <img
                        src={character.profile_image_url}
                        alt={character.name}
                        className="w-12 h-12 rounded-lg object-cover ml-3"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] ml-3 flex items-center justify-center text-white font-semibold">
                        {character.name.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <StatusChip
                      status={
                        character.status === "active"
                          ? "success"
                          : character.status === "error"
                          ? "error"
                          : "warning"
                      }
                      label={character.status}
                    />
                    <span className="text-xs text-[var(--text-muted)]">
                      {new Date(character.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<Users className="h-12 w-12" />}
              title="No characters yet"
              description="Create your first AI influencer character to get started."
              action={{
                label: "Create Character",
                onClick: () => router.push("/characters/create"),
              }}
            />
          )}
        </SectionCard>

        {/* System Status Dashboard */}
        <SectionCard
          title="System Status"
          description="Monitor service health and system resources"
          action={
            status && (
              <div className="flex items-center gap-2">
                <StatusChip
                  status={
                    status.overall_status === "ok"
                      ? "success"
                      : status.overall_status
                  }
                />
                <IconButton
                  icon={<RefreshCw className="h-4 w-4" />}
                  size="sm"
                  variant="ghost"
                  onClick={loadStatus}
                  aria-label="Refresh status"
                />
              </div>
            )
          }
          loading={loading && !status}
          className="mb-8"
        >
          {status && (
            <>
              {/* Service Status Cards */}
              <div className="mb-6 grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                <ServiceCard
                  title="Backend"
                  status={getServiceStatus("backend")}
                  details={status.backend.message}
                  icon={<Settings className="h-5 w-5" />}
                  port={status.backend.port}
                  processId={status.backend.process_id}
                  health={status.backend.state}
                />
                <ServiceCard
                  title="Frontend"
                  status={getServiceStatus("frontend")}
                  details={status.frontend.message}
                  icon={<Activity className="h-5 w-5" />}
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
                  icon={<Sparkles className="h-5 w-5" />}
                  port={status.comfyui_service.port}
                  processId={status.comfyui_service.process_id}
                  health={status.comfyui_service.state}
                />
              </div>

              {/* System Information */}
              <div className="mb-6 grid gap-4 grid-cols-2 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4">
                  <div className="text-xs font-medium text-[var(--text-secondary)]">
                    OS
                  </div>
                  <div className="mt-1 text-sm font-semibold text-[var(--text-primary)]">
                    {status.system.os.system} {status.system.os.release}
                  </div>
                </div>
                <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4">
                  <div className="text-xs font-medium text-[var(--text-secondary)]">
                    Python
                  </div>
                  <div className="mt-1 text-sm font-semibold text-[var(--text-primary)]">
                    {status.system.python.version}
                    {status.system.python.supported ? " ✓" : " ✗"}
                  </div>
                </div>
                <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4">
                  <div className="text-xs font-medium text-[var(--text-secondary)]">
                    Disk Space
                  </div>
                  <div className="mt-1 text-sm font-semibold text-[var(--text-primary)]">
                    {status.system.resources.disk_free_gb.toFixed(1)} GB free
                  </div>
                </div>
                <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4">
                  <div className="text-xs font-medium text-[var(--text-secondary)]">
                    GPU
                  </div>
                  <div className="mt-1 text-sm font-semibold text-[var(--text-primary)]">
                    {status.system.gpu.nvidia_smi ? "NVIDIA ✓" : "Not detected"}
                  </div>
                </div>
              </div>

              {/* Issues */}
              {status.system.issues.length > 0 && (
                <Alert
                  title="System Issues"
                  message={status.system.issues
                    .map((issue) => `${issue.title}: ${issue.detail}`)
                    .join("; ")}
                  variant="warning"
                />
              )}
            </>
          )}
        </SectionCard>

        {/* Error Aggregation Panel */}
        <SectionCard
          title="Error Log"
          description="Track and monitor system errors"
          action={
            errorAggregation && (
              <IconButton
                icon={<RefreshCw className="h-4 w-4" />}
                size="sm"
                variant="ghost"
                onClick={loadErrors}
                aria-label="Refresh errors"
              />
            )
          }
          loading={errorsLoading && !errorAggregation}
          className="mb-8"
        >
          {errorAggregation && (
            <>
              {/* Error Aggregation Stats */}
              <div className="mb-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <MetricCard
                  label="Total Errors"
                  value={errorAggregation.total}
                  variant="default"
                />
                <MetricCard
                  label="Last 24h"
                  value={errorAggregation.recent_count}
                  variant="default"
                />
                <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4">
                  <div className="text-xs font-medium text-[var(--text-secondary)] mb-2">
                    By Level
                  </div>
                  <div className="space-y-1">
                    {Object.entries(errorAggregation.by_level).map(
                      ([level, count]) => (
                        <div key={level} className="text-sm">
                          <span className="font-medium capitalize text-[var(--text-primary)]">
                            {level}:
                          </span>{" "}
                          <span className="text-[var(--text-secondary)]">
                            {count}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                </div>
                <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4">
                  <div className="text-xs font-medium text-[var(--text-secondary)] mb-2">
                    By Source
                  </div>
                  <div className="space-y-1">
                    {Object.entries(errorAggregation.by_source).map(
                      ([source, count]) => (
                        <div key={source} className="text-sm">
                          <span className="font-medium capitalize text-[var(--text-primary)]">
                            {source}:
                          </span>{" "}
                          <span className="text-[var(--text-secondary)]">
                            {count}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                </div>
              </div>

              {/* Recent Errors List */}
              {recentErrors.length > 0 && (
                <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-surface)] p-4">
                  <div className="mb-3 text-sm font-semibold text-[var(--text-primary)]">
                    Recent Errors
                  </div>
                  <div className="space-y-2">
                    {recentErrors.map((err, idx) => (
                      <div
                        key={idx}
                        className="rounded border border-[var(--border-base)] bg-[var(--bg-elevated)] p-3 text-xs"
                      >
                        <div className="mb-1 flex items-center justify-between">
                          <StatusChip
                            status={
                              err.level === "error"
                                ? "error"
                                : err.level === "warning"
                                ? "warning"
                                : "info"
                            }
                            label={err.level.toUpperCase()}
                          />
                          <span className="text-[var(--text-muted)]">
                            {new Date(err.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <div className="mb-1">
                          <span className="font-medium text-[var(--text-primary)]">
                            Source:
                          </span>{" "}
                          <span className="text-[var(--text-secondary)]">
                            {err.source}
                          </span>
                        </div>
                        <div className="text-[var(--text-primary)]">
                          {err.message}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {recentErrors.length === 0 && errorAggregation.total === 0 && (
                <Alert
                  message="No errors logged"
                  variant="success"
                  className="text-center"
                />
              )}
            </>
          )}
        </SectionCard>

        {/* Logs Viewer Panel */}
        <SectionCard
          id="logs-section"
          title="System Logs"
          description="Real-time system activity and events"
          action={
            <div className="flex items-center gap-2">
              {logsMeta && (
                <>
                  <select
                    value={logsFilter.source || ""}
                    onChange={(e) =>
                      setLogsFilter({
                        ...logsFilter,
                        source: e.target.value || null,
                      })
                    }
                    className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] px-2 py-1 text-xs text-[var(--text-primary)]"
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
                    onChange={(e) =>
                      setLogsFilter({
                        ...logsFilter,
                        level: e.target.value || null,
                      })
                    }
                    className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] px-2 py-1 text-xs text-[var(--text-primary)]"
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
                <IconButton
                  icon={<Copy className="h-4 w-4" />}
                  size="sm"
                  variant="ghost"
                  onClick={async () => {
                    const logText = logs
                      .map((log) => {
                        const timestamp = new Date(
                          log.timestamp * 1000
                        ).toLocaleString();
                        return `${timestamp} [${log.level.toUpperCase()}] [${
                          log.source
                        }] ${log.message}`;
                      })
                      .join("\n");
                    try {
                      await navigator.clipboard.writeText(logText);
                    } catch (err) {
                      console.error("Failed to copy logs:", err);
                    }
                  }}
                  aria-label="Copy logs"
                />
              )}
              <IconButton
                icon={<RefreshCw className="h-4 w-4" />}
                size="sm"
                variant="ghost"
                onClick={loadLogs}
                aria-label="Refresh logs"
              />
            </div>
          }
          loading={logsLoading && logs.length === 0}
          empty={logs.length === 0 && !logsLoading}
          emptyMessage="No logs available"
          className="mb-8"
        >
          {logs.length > 0 && (
            <div className="max-h-[500px] overflow-auto rounded-lg border border-[var(--border-base)] bg-[var(--bg-base)] p-4">
              <div className="space-y-1 font-mono text-xs">
                {logs.map((log, idx) => {
                  const isError = log.level === "error";
                  const isWarning = log.level === "warning";
                  const timestamp = new Date(
                    log.timestamp * 1000
                  ).toLocaleString();
                  return (
                    <div
                      key={idx}
                      className="break-words leading-5 hover:bg-[var(--bg-surface)] px-2 py-1 rounded transition-colors"
                    >
                      <span className="text-[var(--text-muted)]">
                        {timestamp}
                      </span>
                      <span
                        className={`ml-2 ${
                          isError
                            ? "text-[var(--error)]"
                            : isWarning
                            ? "text-[var(--warning)]"
                            : "text-[var(--text-secondary)]"
                        }`}
                      >
                        [{log.level.toUpperCase()}] [{log.source}]
                      </span>
                      <span className="ml-2 text-[var(--text-primary)]">
                        {log.message}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </SectionCard>

        {/* Quick Actions */}
        <SectionCard
          title="Quick Actions"
          description="Access key features and tools"
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Link
              href="/characters"
              className="group rounded-xl border border-[var(--border-base)] bg-[var(--bg-elevated)] p-5 hover:border-[var(--accent-primary)] hover:shadow-md transition-all"
            >
              <div className="mb-2 text-[var(--accent-primary)]">
                <Users className="h-6 w-6" />
              </div>
              <div className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-primary)] transition-colors">
                Characters
              </div>
              <div className="mt-2 text-xs text-[var(--text-secondary)]">
                Manage AI influencer characters
              </div>
            </Link>

            <Link
              href="/generate"
              className="group rounded-xl border border-[var(--border-base)] bg-[var(--bg-elevated)] p-5 hover:border-[var(--accent-primary)] hover:shadow-md transition-all"
            >
              <div className="mb-2 text-[var(--accent-primary)]">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-primary)] transition-colors">
                Generate
              </div>
              <div className="mt-2 text-xs text-[var(--text-secondary)]">
                Create images with ComfyUI
              </div>
            </Link>

            <Link
              href="/models"
              className="group rounded-xl border border-[var(--border-base)] bg-[var(--bg-elevated)] p-5 hover:border-[var(--accent-primary)] hover:shadow-md transition-all"
            >
              <div className="mb-2 text-[var(--accent-primary)]">
                <Package className="h-6 w-6" />
              </div>
              <div className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-primary)] transition-colors">
                Models
              </div>
              <div className="mt-2 text-xs text-[var(--text-secondary)]">
                Browse and manage AI models
              </div>
            </Link>

            <Link
              href="/analytics"
              className="group rounded-xl border border-[var(--border-base)] bg-[var(--bg-elevated)] p-5 hover:border-[var(--accent-primary)] hover:shadow-md transition-all"
            >
              <div className="mb-2 text-[var(--accent-primary)]">
                <BarChart3 className="h-6 w-6" />
              </div>
              <div className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-primary)] transition-colors">
                Analytics
              </div>
              <div className="mt-2 text-xs text-[var(--text-secondary)]">
                View performance metrics
              </div>
            </Link>

            <Link
              href="/installer"
              className="group rounded-xl border border-[var(--border-base)] bg-[var(--bg-elevated)] p-5 hover:border-[var(--accent-primary)] hover:shadow-md transition-all"
            >
              <div className="mb-2 text-[var(--accent-primary)]">
                <Settings className="h-6 w-6" />
              </div>
              <div className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-primary)] transition-colors">
                Settings
              </div>
              <div className="mt-2 text-xs text-[var(--text-secondary)]">
                System setup and configuration
              </div>
            </Link>
          </div>
        </SectionCard>
      </main>
    </div>
  );
}
