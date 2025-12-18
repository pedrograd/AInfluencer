"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet, apiPut, apiDelete } from "@/lib/api";
import {
  PageHeader,
  SectionCard,
  Input,
  Select,
  PrimaryButton,
  SecondaryButton,
  IconButton,
  StatusChip,
  EmptyState,
  LoadingSkeleton,
  Alert,
  ErrorBanner,
} from "@/components/ui";
import {
  UserPlus,
  Grid3x3,
  List,
  Pause,
  Play,
  Edit,
  Trash2,
  Search,
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

type ViewMode = "grid" | "table";

export default function CharactersPage() {
  const router = useRouter();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [total, setTotal] = useState(0);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchCharacters = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      if (search) {
        params.append("search", search);
      }
      if (statusFilter !== "all") {
        params.append("status", statusFilter);
      }
      params.append("limit", "50");
      params.append("offset", "0");

      const response = await apiGet<CharactersResponse>(
        `/api/characters?${params.toString()}`
      );
      if (response.success) {
        setCharacters(response.data.characters);
        setTotal(response.data.total);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load characters"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharacters();
  }, [search, statusFilter]);

  const handlePauseResume = async (
    characterId: string,
    currentStatus: string
  ) => {
    try {
      setActionLoading(characterId);
      const newStatus = currentStatus === "active" ? "paused" : "active";
      await apiPut(`/api/characters/${characterId}`, { status: newStatus });
      await fetchCharacters();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update character status"
      );
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (characterId: string, characterName: string) => {
    if (
      !confirm(
        `Are you sure you want to delete "${characterName}"? This action cannot be undone.`
      )
    ) {
      return;
    }
    try {
      setActionLoading(characterId);
      await apiDelete(`/api/characters/${characterId}`);
      await fetchCharacters();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete character"
      );
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusChipStatus = (
    status: string
  ): "success" | "warning" | "error" | "info" => {
    switch (status) {
      case "active":
        return "success";
      case "paused":
        return "warning";
      case "error":
        return "error";
      default:
        return "info";
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        <PageHeader
          title="Characters"
          description="Manage your AI influencer characters"
          action={
            <PrimaryButton
              icon={<UserPlus className="h-4 w-4" />}
              onClick={() => router.push("/characters/create")}
            >
              Create Character
            </PrimaryButton>
          }
        />

        {/* Filters and Search */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search characters by name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="h-4 w-4" />}
            />
          </div>
          <div className="w-full sm:w-48">
            <Select
              options={[
                { value: "all", label: "All Status" },
                { value: "active", label: "Active" },
                { value: "paused", label: "Paused" },
                { value: "error", label: "Error" },
              ]}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <IconButton
              icon={<Grid3x3 className="h-4 w-4" />}
              size="md"
              variant={viewMode === "grid" ? "primary" : "ghost"}
              onClick={() => setViewMode("grid")}
              aria-label="Grid view"
            />
            <IconButton
              icon={<List className="h-4 w-4" />}
              size="md"
              variant={viewMode === "table" ? "primary" : "ghost"}
              onClick={() => setViewMode("table")}
              aria-label="Table view"
            />
          </div>
        </div>

        {error && (
          <div className="mb-6">
            <ErrorBanner
              title="Error loading characters"
              message={error}
              remediation={{
                label: "Retry",
                onClick: fetchCharacters,
              }}
            />
          </div>
        )}

        <SectionCard
          title={`Showing ${characters.length} of ${total} characters`}
          loading={loading}
          empty={!loading && characters.length === 0}
          emptyMessage="No characters found"
        >
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <LoadingSkeleton key={i} variant="card" height="300px" />
              ))}
            </div>
          ) : characters.length === 0 ? (
            <EmptyState
              icon={<UserPlus className="h-12 w-12" />}
              title="No characters found"
              description={
                search || statusFilter !== "all"
                  ? "Try adjusting your search or filters"
                  : "Create your first AI influencer character to get started"
              }
              action={{
                label: "Create Character",
                onClick: () => router.push("/characters/create"),
              }}
            />
          ) : viewMode === "grid" ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {characters.map((character) => (
                <div
                  key={character.id}
                  className="rounded-xl border border-[var(--border-base)] bg-[var(--bg-elevated)] p-6 hover:border-[var(--accent-primary)] hover:shadow-lg transition-all"
                >
                  <Link
                    href={`/characters/${character.id}`}
                    className="block mb-4"
                  >
                    {character.profile_image_url ? (
                      <img
                        src={character.profile_image_url}
                        alt={character.name}
                        className="w-full h-48 object-cover rounded-lg"
                      />
                    ) : (
                      <div className="w-full h-48 bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] rounded-lg flex items-center justify-center">
                        <span className="text-4xl text-white font-bold">
                          {character.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                  </Link>

                  <div>
                    <Link href={`/characters/${character.id}`}>
                      <h3 className="text-lg font-semibold mb-2 truncate hover:text-[var(--accent-primary)] transition-colors text-[var(--text-primary)]">
                        {character.name}
                      </h3>
                    </Link>
                    {character.bio && (
                      <p className="text-[var(--text-secondary)] text-sm mb-3 line-clamp-2">
                        {character.bio}
                      </p>
                    )}
                    <div className="flex items-center justify-between mb-3">
                      <StatusChip
                        status={getStatusChipStatus(character.status)}
                        label={character.status}
                      />
                      <span className="text-xs text-[var(--text-muted)]">
                        {new Date(character.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex gap-2 pt-3 border-t border-[var(--border-base)]">
                      <SecondaryButton
                        size="sm"
                        icon={
                          character.status === "active" ? (
                            <Pause className="h-3 w-3" />
                          ) : (
                            <Play className="h-3 w-3" />
                          )
                        }
                        onClick={() =>
                          handlePauseResume(character.id, character.status)
                        }
                        disabled={actionLoading === character.id}
                        loading={actionLoading === character.id}
                        className="flex-1"
                      >
                        {character.status === "active" ? "Pause" : "Resume"}
                      </SecondaryButton>
                      <Link
                        href={`/characters/${character.id}/edit`}
                        className="flex-1"
                      >
                        <SecondaryButton
                          size="sm"
                          icon={<Edit className="h-3 w-3" />}
                          className="w-full"
                        >
                          Edit
                        </SecondaryButton>
                      </Link>
                      <IconButton
                        icon={<Trash2 className="h-4 w-4" />}
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          handleDelete(character.id, character.name)
                        }
                        disabled={actionLoading === character.id}
                        aria-label="Delete character"
                        className="text-[var(--error)] hover:bg-[var(--error-bg)]"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] overflow-hidden overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <thead className="bg-[var(--bg-surface)]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                      Avatar
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider hidden sm:table-cell">
                      Bio
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider hidden md:table-cell">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-base)]">
                  {characters.map((character) => (
                    <tr
                      key={character.id}
                      className="hover:bg-[var(--bg-surface)] transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link href={`/characters/${character.id}`}>
                          {character.profile_image_url ? (
                            <img
                              src={character.profile_image_url}
                              alt={character.name}
                              className="w-12 h-12 object-cover rounded-lg"
                            />
                          ) : (
                            <div className="w-12 h-12 bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] rounded-lg flex items-center justify-center">
                              <span className="text-lg text-white font-bold">
                                {character.name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          )}
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link
                          href={`/characters/${character.id}`}
                          className="text-sm font-medium text-[var(--text-primary)] hover:text-[var(--accent-primary)] transition-colors"
                        >
                          {character.name}
                        </Link>
                      </td>
                      <td className="px-6 py-4 hidden sm:table-cell">
                        <p className="text-sm text-[var(--text-secondary)] max-w-md truncate">
                          {character.bio || "—"}
                        </p>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusChip
                          status={getStatusChipStatus(character.status)}
                          label={character.status}
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-muted)] hidden md:table-cell">
                        {new Date(character.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <SecondaryButton
                            size="sm"
                            icon={
                              character.status === "active" ? (
                                <Pause className="h-3 w-3" />
                              ) : (
                                <Play className="h-3 w-3" />
                              )
                            }
                            onClick={() =>
                              handlePauseResume(character.id, character.status)
                            }
                            disabled={actionLoading === character.id}
                            loading={actionLoading === character.id}
                          >
                            {character.status === "active" ? "Pause" : "Resume"}
                          </SecondaryButton>
                          <Link href={`/characters/${character.id}/edit`}>
                            <SecondaryButton
                              size="sm"
                              icon={<Edit className="h-3 w-3" />}
                            >
                              Edit
                            </SecondaryButton>
                          </Link>
                          <IconButton
                            icon={<Trash2 className="h-4 w-4" />}
                            size="sm"
                            variant="ghost"
                            onClick={() =>
                              handleDelete(character.id, character.name)
                            }
                            disabled={actionLoading === character.id}
                            aria-label="Delete character"
                            className="text-[var(--error)] hover:bg-[var(--error-bg)]"
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </main>
    </div>
  );
}
