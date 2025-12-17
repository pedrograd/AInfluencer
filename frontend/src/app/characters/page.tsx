"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet, apiPut, apiDelete } from "@/lib/api";

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
      setError(err instanceof Error ? err.message : "Failed to load characters");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharacters();
  }, [search, statusFilter]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "paused":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      case "error":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  const handlePauseResume = async (characterId: string, currentStatus: string) => {
    try {
      setActionLoading(characterId);
      const newStatus = currentStatus === "active" ? "paused" : "active";
      await apiPut(`/api/characters/${characterId}`, { status: newStatus });
      await fetchCharacters();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update character status");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (characterId: string, characterName: string) => {
    if (!confirm(`Are you sure you want to delete "${characterName}"? This action cannot be undone.`)) {
      return;
    }
    try {
      setActionLoading(characterId);
      await apiDelete(`/api/characters/${characterId}`);
      await fetchCharacters();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete character");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold mb-2">Characters</h1>
            <p className="text-slate-400">
              Manage your AI influencer characters
            </p>
          </div>
          <Link
            href="/characters/create"
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
          >
            Create New Character
          </Link>
        </div>

        {/* Filters, Search, and View Toggle */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search characters by name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="error">Error</option>
          </select>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode("grid")}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                viewMode === "grid"
                  ? "bg-indigo-600 border-indigo-500 text-white"
                  : "bg-slate-800 border-slate-700 text-slate-100 hover:bg-slate-700"
              }`}
              title="Grid View"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                viewMode === "table"
                  ? "bg-indigo-600 border-indigo-500 text-white"
                  : "bg-slate-800 border-slate-700 text-slate-100 hover:bg-slate-700"
              }`}
              title="Table View"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
            <p className="mt-4 text-slate-400">Loading characters...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4 mb-6">
            <p className="text-red-400">Error: {error}</p>
            <button
              onClick={fetchCharacters}
              className="mt-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Characters Display */}
        {!loading && !error && (
          <>
            <div className="mb-4 text-slate-400">
              Showing {characters.length} of {total} characters
            </div>
            {characters.length === 0 ? (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
                <p className="text-slate-400 mb-4">No characters found</p>
                <Link
                  href="/characters/create"
                  className="inline-block px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
                >
                  Create Your First Character
                </Link>
              </div>
            ) : viewMode === "grid" ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {characters.map((character) => (
                  <div
                    key={character.id}
                    className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-indigo-500/50 transition-all hover:shadow-lg hover:shadow-indigo-500/10"
                  >
                    {/* Character Avatar */}
                    <Link href={`/characters/${character.id}`} className="block mb-4">
                      {character.profile_image_url ? (
                        <img
                          src={character.profile_image_url}
                          alt={character.name}
                          className="w-full h-48 object-cover rounded-lg"
                        />
                      ) : (
                        <div className="w-full h-48 bg-slate-700 rounded-lg flex items-center justify-center">
                          <span className="text-4xl text-slate-500">
                            {character.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      )}
                    </Link>

                    {/* Character Info */}
                    <div>
                      <Link href={`/characters/${character.id}`}>
                        <h3 className="text-xl font-semibold mb-2 truncate hover:text-indigo-400 transition-colors">
                          {character.name}
                        </h3>
                      </Link>
                      {character.bio && (
                        <p className="text-slate-400 text-sm mb-3 line-clamp-2">
                          {character.bio}
                        </p>
                      )}
                      <div className="flex items-center justify-between mb-3">
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(
                            character.status
                          )}`}
                        >
                          {character.status}
                        </span>
                        <span className="text-xs text-slate-500">
                          {new Date(character.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      {/* Quick Actions */}
                      <div className="flex gap-2 pt-3 border-t border-slate-700">
                        <button
                          onClick={() => handlePauseResume(character.id, character.status)}
                          disabled={actionLoading === character.id}
                          className="flex-1 px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-100 rounded transition-colors disabled:opacity-50"
                          title={character.status === "active" ? "Pause" : "Resume"}
                        >
                          {actionLoading === character.id ? "..." : character.status === "active" ? "Pause" : "Resume"}
                        </button>
                        <Link
                          href={`/characters/${character.id}/edit`}
                          className="flex-1 px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-100 rounded transition-colors text-center"
                        >
                          Edit
                        </Link>
                        <button
                          onClick={() => handleDelete(character.id, character.name)}
                          disabled={actionLoading === character.id}
                          className="px-3 py-1.5 text-xs bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded transition-colors disabled:opacity-50"
                          title="Delete"
                        >
                          🗑
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-slate-700/50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Avatar</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Bio</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Created</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-slate-300 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700">
                    {characters.map((character) => (
                      <tr key={character.id} className="hover:bg-slate-700/30 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Link href={`/characters/${character.id}`}>
                            {character.profile_image_url ? (
                              <img
                                src={character.profile_image_url}
                                alt={character.name}
                                className="w-12 h-12 object-cover rounded-lg"
                              />
                            ) : (
                              <div className="w-12 h-12 bg-slate-700 rounded-lg flex items-center justify-center">
                                <span className="text-lg text-slate-500">
                                  {character.name.charAt(0).toUpperCase()}
                                </span>
                              </div>
                            )}
                          </Link>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Link href={`/characters/${character.id}`} className="text-slate-100 font-medium hover:text-indigo-400 transition-colors">
                            {character.name}
                          </Link>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-sm text-slate-400 max-w-md truncate">
                            {character.bio || "—"}
                          </p>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(
                              character.status
                            )}`}
                          >
                            {character.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                          {new Date(character.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handlePauseResume(character.id, character.status)}
                              disabled={actionLoading === character.id}
                              className="px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-100 rounded transition-colors disabled:opacity-50"
                              title={character.status === "active" ? "Pause" : "Resume"}
                            >
                              {actionLoading === character.id ? "..." : character.status === "active" ? "Pause" : "Resume"}
                            </button>
                            <Link
                              href={`/characters/${character.id}/edit`}
                              className="px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-100 rounded transition-colors"
                            >
                              Edit
                            </Link>
                            <button
                              onClick={() => handleDelete(character.id, character.name)}
                              disabled={actionLoading === character.id}
                              className="px-3 py-1.5 text-xs bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded transition-colors disabled:opacity-50"
                              title="Delete"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

