"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet, apiDelete, apiPost } from "@/lib/api";

type VideoItem = {
  filename: string;
  size_bytes: number;
  size_mb: number;
  created_at: string;
  modified_at: string;
  thumbnail_url?: string | null;
};

type VideoListResponse = {
  items: VideoItem[];
  total: number;
  limit: number;
  offset: number;
  sort: string;
  q: string | null;
};

type StorageStats = {
  videos_count: number;
  videos_bytes: number;
  videos_mb: number;
  videos_gb: number;
};

export default function VideosPage() {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [stats, setStats] = useState<StorageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<"newest" | "oldest" | "name">("newest");
  const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState<string | null>(null);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [cleanupDays, setCleanupDays] = useState(30);
  const [cleanupRunning, setCleanupRunning] = useState(false);
  const [generatingThumbnails, setGeneratingThumbnails] = useState<Set<string>>(new Set());

  async function loadVideos() {
    try {
      setError(null);
      setLoading(true);
      const params = new URLSearchParams();
      if (query) params.set("q", query);
      params.set("sort", sort);
      params.set("limit", "50");
      params.set("offset", "0");

      const data = await apiGet<VideoListResponse>(`/api/content/videos?${params.toString()}`);
      setVideos(data.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function loadStats() {
    try {
      const data = await apiGet<StorageStats>("/api/content/videos/storage");
      setStats(data);
    } catch (e) {
      console.error("Failed to load stats:", e);
    }
  }

  useEffect(() => {
    void loadVideos();
    void loadStats();
  }, [sort]);

  async function handleDelete(filename: string) {
    if (!confirm(`Delete video "${filename}"?`)) return;

    try {
      setDeleting(filename);
      await apiDelete(`/api/content/videos/${encodeURIComponent(filename)}`);
      await loadVideos();
      await loadStats();
      setSelectedVideos((prev) => {
        const next = new Set(prev);
        next.delete(filename);
        return next;
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setDeleting(null);
    }
  }

  async function handleBulkDelete() {
    if (selectedVideos.size === 0) return;
    if (!confirm(`Delete ${selectedVideos.size} video(s)?`)) return;

    try {
      setBulkDeleting(true);
      await apiPost("/api/content/videos/bulk-delete", {
        filenames: Array.from(selectedVideos),
      });
      await loadVideos();
      await loadStats();
      setSelectedVideos(new Set());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBulkDeleting(false);
    }
  }

  async function handleCleanup() {
    if (!confirm(`Delete videos older than ${cleanupDays} days?`)) return;

    try {
      setCleanupRunning(true);
      await apiPost("/api/content/videos/cleanup", {
        older_than_days: cleanupDays,
      });
      await loadVideos();
      await loadStats();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCleanupRunning(false);
    }
  }

  async function handleDownloadAll() {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/content/videos/download-all`);
      if (!response.ok) throw new Error("Download failed");
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "videos.zip";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleString();
  }

  function toggleSelect(filename: string) {
    setSelectedVideos((prev) => {
      const next = new Set(prev);
      if (next.has(filename)) {
        next.delete(filename);
      } else {
        next.add(filename);
      }
      return next;
    });
  }

  function toggleSelectAll() {
    if (selectedVideos.size === videos.length) {
      setSelectedVideos(new Set());
    } else {
      setSelectedVideos(new Set(videos.map((v) => v.filename)));
    }
  }

  async function generateThumbnail(filename: string) {
    if (generatingThumbnails.has(filename)) return;

    try {
      setGeneratingThumbnails((prev) => new Set(prev).add(filename));

      // Get video URL
      const videoUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/content/videos/${encodeURIComponent(filename)}`;

      // Create video element to capture frame
      const video = document.createElement("video");
      video.crossOrigin = "anonymous";
      video.preload = "metadata";

      await new Promise<void>((resolve, reject) => {
        video.onloadedmetadata = () => {
          video.currentTime = Math.min(1, video.duration / 2); // Seek to middle or 1 second
        };
        video.onseeked = () => resolve();
        video.onerror = () => reject(new Error("Failed to load video"));
        video.src = videoUrl;
      });

      // Capture frame to canvas
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Failed to get canvas context");

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert to blob
      const blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob(
          (b) => {
            if (b) resolve(b);
            else reject(new Error("Failed to create thumbnail"));
          },
          "image/jpeg",
          0.9
        );
      });

      // Upload thumbnail
      const formData = new FormData();
      formData.append("file", blob, `${filename}.jpg`);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/content/videos/${encodeURIComponent(filename)}/thumbnail`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || "Failed to upload thumbnail");
      }

      // Reload videos to get updated thumbnail URL
      await loadVideos();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGeneratingThumbnails((prev) => {
        const next = new Set(prev);
        next.delete(filename);
        return next;
      });
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <div className="mx-auto w-full max-w-6xl px-6 py-10">
        <div className="flex items-start justify-between gap-6">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Video Storage</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
              Manage stored video files: view, search, delete, and download videos.
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
              onClick={() => void loadVideos()}
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

        {/* Storage Stats */}
        {stats ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-zinc-200 bg-white p-5">
              <div className="text-sm font-medium text-zinc-600">Total Videos</div>
              <div className="mt-2 text-2xl font-semibold">{stats.videos_count}</div>
            </div>
            <div className="rounded-xl border border-zinc-200 bg-white p-5">
              <div className="text-sm font-medium text-zinc-600">Total Size</div>
              <div className="mt-2 text-2xl font-semibold">{formatSize(stats.videos_bytes)}</div>
            </div>
            <div className="rounded-xl border border-zinc-200 bg-white p-5">
              <div className="text-sm font-medium text-zinc-600">Storage</div>
              <div className="mt-2 text-2xl font-semibold">
                {stats.videos_gb.toFixed(2)} GB
              </div>
            </div>
          </div>
        ) : null}

        {/* Search and Filters */}
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search videos..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void loadVideos();
              }}
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none"
            />
          </div>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as "newest" | "oldest" | "name")}
            className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="name">Name (A-Z)</option>
          </select>
          <button
            type="button"
            onClick={() => void loadVideos()}
            className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium hover:bg-zinc-50"
          >
            Search
          </button>
        </div>

        {/* Bulk Actions */}
        {selectedVideos.size > 0 ? (
          <div className="mt-4 flex items-center gap-3 rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3">
            <span className="text-sm font-medium text-zinc-700">
              {selectedVideos.size} video(s) selected
            </span>
            <button
              type="button"
              onClick={() => void handleBulkDelete()}
              disabled={bulkDeleting}
              className="ml-auto rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
            >
              {bulkDeleting ? "Deleting..." : "Delete Selected"}
            </button>
            <button
              type="button"
              onClick={() => setSelectedVideos(new Set())}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm font-medium hover:bg-zinc-50"
            >
              Clear Selection
            </button>
          </div>
        ) : null}

        {/* Cleanup and Download All */}
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="1"
              max="3650"
              value={cleanupDays}
              onChange={(e) => setCleanupDays(Number.parseInt(e.target.value, 10))}
              className="w-20 rounded-lg border border-zinc-200 bg-white px-2 py-1.5 text-sm focus:border-zinc-400 focus:outline-none"
            />
            <span className="text-sm text-zinc-600">days old</span>
            <button
              type="button"
              onClick={() => void handleCleanup()}
              disabled={cleanupRunning}
              className="rounded-lg border border-orange-200 bg-orange-50 px-3 py-1.5 text-sm font-medium text-orange-700 hover:bg-orange-100 disabled:opacity-50"
            >
              {cleanupRunning ? "Cleaning..." : "Cleanup Old Videos"}
            </button>
          </div>
          <button
            type="button"
            onClick={() => void handleDownloadAll()}
            className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100"
          >
            Download All as ZIP
          </button>
        </div>

        {/* Video List */}
        <div className="mt-6">
          {loading ? (
            <div className="rounded-lg border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-600">
              Loading videos...
            </div>
          ) : videos.length === 0 ? (
            <div className="rounded-lg border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-600">
              No videos found.
            </div>
          ) : (
            <div className="rounded-lg border border-zinc-200 bg-white">
              <table className="w-full">
                <thead className="border-b border-zinc-200 bg-zinc-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-600">
                      <input
                        type="checkbox"
                        checked={selectedVideos.size === videos.length && videos.length > 0}
                        onChange={toggleSelectAll}
                        className="rounded border-zinc-300"
                      />
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-600">
                      Thumbnail
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-600">
                      Filename
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-600">
                      Size
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-600">
                      Created
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-600">
                      Modified
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-600">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200">
                  {videos.map((video) => (
                    <tr key={video.filename} className="hover:bg-zinc-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedVideos.has(video.filename)}
                          onChange={() => toggleSelect(video.filename)}
                          className="rounded border-zinc-300"
                        />
                      </td>
                      <td className="px-4 py-3">
                        {video.thumbnail_url ? (
                          <img
                            src={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}${video.thumbnail_url}`}
                            alt={video.filename}
                            className="h-16 w-28 rounded border border-zinc-200 object-cover"
                          />
                        ) : (
                          <div className="flex h-16 w-28 items-center justify-center rounded border border-zinc-200 bg-zinc-50">
                            {generatingThumbnails.has(video.filename) ? (
                              <span className="text-xs text-zinc-500">Generating...</span>
                            ) : (
                              <button
                                type="button"
                                onClick={() => void generateThumbnail(video.filename)}
                                className="text-xs text-blue-600 hover:text-blue-700"
                              >
                                Generate
                              </button>
                            )}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium">{video.filename}</td>
                      <td className="px-4 py-3 text-sm text-zinc-600">{formatSize(video.size_bytes)}</td>
                      <td className="px-4 py-3 text-sm text-zinc-600">{formatDate(video.created_at)}</td>
                      <td className="px-4 py-3 text-sm text-zinc-600">{formatDate(video.modified_at)}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => void handleDelete(video.filename)}
                          disabled={deleting === video.filename}
                          className="rounded-lg border border-red-200 bg-red-50 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
                        >
                          {deleting === video.filename ? "Deleting..." : "Delete"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

