"use client";

import { useEffect, useState, useMemo } from "react";
import { API_BASE_URL, apiGet, apiDelete, apiPost } from "@/lib/api";
import {
  PageHeader,
  SectionCard,
  PrimaryButton,
  SecondaryButton,
  IconButton,
  Input,
  Select,
  StatusChip,
  LoadingSkeleton,
  EmptyState,
  Alert,
  ErrorBanner,
  MetricCard,
} from "@/components/ui";
import {
  Image as ImageIcon,
  Video,
  Download,
  Trash2,
  RefreshCw,
  Search,
  Filter,
  X,
  Grid3x3,
  List,
} from "lucide-react";

type ContentItem = {
  id: string;
  character_id: string | null;
  character_name: string | null;
  content_type: string;
  content_category: string | null;
  file_url: string | null;
  file_path: string | null;
  thumbnail_url: string | null;
  thumbnail_path: string | null;
  file_size: number | null;
  width: number | null;
  height: number | null;
  prompt: string | null;
  negative_prompt: string | null;
  quality_score: number | null;
  is_approved: boolean;
  approval_status: string | null;
  is_nsfw: boolean;
  description: string | null;
  tags: string[] | null;
  folder_path: string | null;
  created_at: string | null;
};

type ContentLibraryResponse = {
  ok: boolean;
  items: ContentItem[];
  total: number;
  limit: number;
  offset: number;
  error?: string;
};

type ImageItem = {
  path: string;
  mtime: number;
  size_bytes: number;
  url: string;
};

type VideoItem = {
  filename: string;
  size_bytes: number;
  size_mb: number;
  created_at: string;
  modified_at: string;
  thumbnail_url?: string | null;
};

type ViewMode = "grid" | "table";

export default function LibraryPage() {
  const [contentItems, setContentItems] = useState<ContentItem[]>([]);
  const [images, setImages] = useState<ImageItem[]>([]);
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [contentType, setContentType] = useState<"all" | "image" | "video">(
    "all"
  );
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<"newest" | "oldest" | "name">("newest");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [limit] = useState(48);
  const [hasMore, setHasMore] = useState(false);

  async function loadContent() {
    try {
      setLoading(true);
      setError(null);

      if (contentType === "all" || contentType === "image") {
        // Load images
        const params = new URLSearchParams({
          q: search.trim(),
          sort: sort,
          limit: String(limit),
          offset: String(offset),
        });
        const imagesData = await apiGet<{
          items: ImageItem[];
          total: number;
          limit: number;
          offset: number;
        }>(`/api/content/images?${params.toString()}`);
        setImages(imagesData.items || []);
      }

      if (contentType === "all" || contentType === "video") {
        // Load videos
        const params = new URLSearchParams();
        if (search) params.set("q", search);
        params.set("sort", sort);
        params.set("limit", String(limit));
        params.set("offset", String(offset));
        const videosData = await apiGet<{
          items: VideoItem[];
          total: number;
          limit: number;
          offset: number;
        }>(`/api/content/videos?${params.toString()}`);
        setVideos(videosData.items || []);
      }

      // Also try to load from unified library API
      try {
        const params = new URLSearchParams();
        if (contentType !== "all") {
          params.append("content_type", contentType);
        }
        if (search) params.append("search", search);
        params.append("limit", String(limit));
        params.append("offset", String(offset));
        const libraryData = await apiGet<ContentLibraryResponse>(
          `/api/content/library?${params.toString()}`
        );
        if (libraryData.ok) {
          setContentItems(libraryData.items || []);
          setTotal(libraryData.total || 0);
          setHasMore(
            (libraryData.offset || 0) + (libraryData.limit || limit) <
              (libraryData.total || 0)
          );
        }
      } catch (e) {
        // Fallback to separate endpoints
        console.log("Library API not available, using separate endpoints");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load content");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadContent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentType, search, sort]);

  useEffect(() => {
    setOffset(0);
    setSelectedItems(new Set());
    loadContent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentType, search, sort]);

  async function loadMore() {
    const newOffset = offset + limit;
    setOffset(newOffset);
    try {
      if (contentType === "all" || contentType === "image") {
        const params = new URLSearchParams({
          q: search.trim(),
          sort: sort,
          limit: String(limit),
          offset: String(newOffset),
        });
        const imagesData = await apiGet<{
          items: ImageItem[];
          total: number;
        }>(`/api/content/images?${params.toString()}`);
        setImages((prev) => [...prev, ...(imagesData.items || [])]);
      }

      if (contentType === "all" || contentType === "video") {
        const params = new URLSearchParams();
        if (search) params.set("q", search);
        params.set("sort", sort);
        params.set("limit", String(limit));
        params.set("offset", String(newOffset));
        const videosData = await apiGet<{
          items: VideoItem[];
          total: number;
        }>(`/api/content/videos?${params.toString()}`);
        setVideos((prev) => [...prev, ...(videosData.items || [])]);
      }
    } catch (e) {
      console.error("Failed to load more:", e);
    }
  }

  async function handleDelete(itemId: string, type: "image" | "video") {
    if (!confirm("Are you sure you want to delete this item?")) return;

    try {
      setIsDeleting(itemId);
      if (type === "image") {
        await apiDelete(`/api/content/images/${encodeURIComponent(itemId)}`);
      } else {
        await apiDelete(`/api/content/videos/${encodeURIComponent(itemId)}`);
      }
      await loadContent();
      setSelectedItems((prev) => {
        const next = new Set(prev);
        next.delete(itemId);
        return next;
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete");
    } finally {
      setIsDeleting(null);
    }
  }

  async function handleBulkDelete() {
    if (selectedItems.size === 0) return;
    if (!confirm(`Delete ${selectedItems.size} item(s)?`)) return;

    try {
      setIsBulkDeleting(true);
      const imagePaths = Array.from(selectedItems).filter((id) =>
        images.some((img) => img.path === id)
      );
      const videoFilenames = Array.from(selectedItems).filter((id) =>
        videos.some((vid) => vid.filename === id)
      );

      if (imagePaths.length > 0) {
        await apiPost("/api/content/images/delete", {
          filenames: imagePaths,
        });
      }

      if (videoFilenames.length > 0) {
        await apiPost("/api/content/videos/bulk-delete", {
          filenames: videoFilenames,
        });
      }

      setSelectedItems(new Set());
      await loadContent();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete");
    } finally {
      setIsBulkDeleting(false);
    }
  }

  function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024)
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  }

  const allItems = useMemo(() => {
    const items: Array<{
      id: string;
      type: "image" | "video";
      thumbnail?: string;
      url: string;
      name: string;
      size?: number;
      created?: string;
      data: ImageItem | VideoItem;
    }> = [];

    if (contentType === "all" || contentType === "image") {
      images.forEach((img) => {
        items.push({
          id: img.path,
          type: "image",
          thumbnail: `${API_BASE_URL}${img.url}`,
          url: `${API_BASE_URL}${img.url}`,
          name: img.path,
          size: img.size_bytes,
          created: new Date(img.mtime * 1000).toISOString(),
          data: img,
        });
      });
    }

    if (contentType === "all" || contentType === "video") {
      videos.forEach((vid) => {
        items.push({
          id: vid.filename,
          type: "video",
          thumbnail: vid.thumbnail_url
            ? `${API_BASE_URL}${vid.thumbnail_url}`
            : undefined,
          url: `${API_BASE_URL}/content/videos/${encodeURIComponent(
            vid.filename
          )}`,
          name: vid.filename,
          size: vid.size_bytes,
          created: vid.created_at,
          data: vid,
        });
      });
    }

    // Sort items
    items.sort((a, b) => {
      if (sort === "newest") {
        return (
          new Date(b.created || 0).getTime() -
          new Date(a.created || 0).getTime()
        );
      } else if (sort === "oldest") {
        return (
          new Date(a.created || 0).getTime() -
          new Date(b.created || 0).getTime()
        );
      } else {
        return a.name.localeCompare(b.name);
      }
    });

    return items;
  }, [images, videos, contentType, sort]);

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        <PageHeader
          title="Library"
          description="View and manage all generated content (images and videos)"
          action={
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
          }
        />

        {/* Stats */}
        <div className="mb-6 grid gap-4 grid-cols-1 sm:grid-cols-3">
          <MetricCard
            label="Total Images"
            value={images.length}
            icon={<ImageIcon className="h-5 w-5" />}
            variant="icon"
          />
          <MetricCard
            label="Total Videos"
            value={videos.length}
            icon={<Video className="h-5 w-5" />}
            variant="icon"
          />
          <MetricCard
            label="Total Content"
            value={allItems.length}
            icon={<ImageIcon className="h-5 w-5" />}
            variant="icon"
          />
        </div>

        {error && (
          <div className="mb-6">
            <ErrorBanner
              title="Error loading content"
              message={error}
              remediation={{
                label: "Retry",
                onClick: loadContent,
              }}
            />
          </div>
        )}

        {/* Filters */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search content..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="h-4 w-4" />}
            />
          </div>
          <div className="w-full sm:w-48">
            <Select
              label="Type"
              options={[
                { value: "all", label: "All Types" },
                { value: "image", label: "Images" },
                { value: "video", label: "Videos" },
              ]}
              value={contentType}
              onChange={(e) =>
                setContentType(e.target.value as typeof contentType)
              }
            />
          </div>
          <div className="w-full sm:w-48">
            <Select
              label="Sort"
              options={[
                { value: "newest", label: "Newest First" },
                { value: "oldest", label: "Oldest First" },
                { value: "name", label: "Name (A-Z)" },
              ]}
              value={sort}
              onChange={(e) => setSort(e.target.value as typeof sort)}
            />
          </div>
        </div>

        {/* Bulk Actions */}
        {selectedItems.size > 0 && (
          <div className="mb-6">
            <Alert
              title={`${selectedItems.size} item(s) selected`}
              message="Choose an action to perform on selected items"
              variant="info"
              action={{
                label: "Delete Selected",
                onClick: handleBulkDelete,
              }}
              dismissible
              onDismiss={() => setSelectedItems(new Set())}
            />
          </div>
        )}

        <SectionCard
          title={`Showing ${allItems.length} items`}
          loading={loading && allItems.length === 0}
          empty={!loading && allItems.length === 0}
          emptyMessage="No content found"
        >
          {loading && allItems.length === 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <LoadingSkeleton key={i} variant="image" height="200px" />
              ))}
            </div>
          ) : allItems.length === 0 ? (
            <EmptyState
              icon={<ImageIcon className="h-12 w-12" />}
              title="No content found"
              description={
                search || contentType !== "all"
                  ? "Try adjusting your search or filters"
                  : "Generate images or videos to see them here"
              }
              action={{
                label: "Go to Generate",
                onClick: () => (window.location.href = "/generate"),
              }}
            />
          ) : viewMode === "grid" ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {allItems.map((item) => (
                <div
                  key={item.id}
                  className="group rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] overflow-hidden hover:border-[var(--accent-primary)] transition-all"
                >
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block"
                  >
                    {item.thumbnail ? (
                      <img
                        src={item.thumbnail}
                        alt={item.name}
                        className="aspect-square w-full object-cover"
                      />
                    ) : (
                      <div className="aspect-square w-full bg-[var(--bg-surface)] flex items-center justify-center">
                        {item.type === "image" ? (
                          <ImageIcon className="h-12 w-12 text-[var(--text-muted)]" />
                        ) : (
                          <Video className="h-12 w-12 text-[var(--text-muted)]" />
                        )}
                      </div>
                    )}
                  </a>
                  <div className="p-3 border-t border-[var(--border-base)]">
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex-1 min-w-0">
                        <p
                          className="text-xs text-[var(--text-primary)] truncate"
                          title={item.name}
                        >
                          {item.name}
                        </p>
                        {item.size && (
                          <p className="text-[10px] text-[var(--text-muted)]">
                            {formatBytes(item.size)}
                          </p>
                        )}
                      </div>
                      <StatusChip
                        status="info"
                        label={item.type}
                        className="text-[10px]"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="flex items-center gap-1 text-[10px] text-[var(--text-secondary)] cursor-pointer flex-1">
                        <input
                          type="checkbox"
                          checked={selectedItems.has(item.id)}
                          onChange={(e) => {
                            const checked = e.target.checked;
                            setSelectedItems((prev) => {
                              const next = new Set(prev);
                              if (checked) {
                                next.add(item.id);
                              } else {
                                next.delete(item.id);
                              }
                              return next;
                            });
                          }}
                          className="w-3 h-3 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
                        />
                        Select
                      </label>
                      <IconButton
                        icon={<Trash2 className="h-3 w-3" />}
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(item.id, item.type)}
                        disabled={isDeleting === item.id}
                        aria-label="Delete"
                        className="text-[var(--error)] hover:bg-[var(--error-bg)]"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] overflow-hidden overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-[var(--bg-surface)]">
                  <tr>
                    <th className="px-6 py-3">
                      <input
                        type="checkbox"
                        checked={
                          selectedItems.size === allItems.length &&
                          allItems.length > 0
                        }
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedItems(
                              new Set(allItems.map((item) => item.id))
                            );
                          } else {
                            setSelectedItems(new Set());
                          }
                        }}
                        className="w-4 h-4 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
                      />
                    </th>
                    <th className="px-6 py-3 text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                      Thumbnail
                    </th>
                    <th className="px-6 py-3 text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-3 text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-base)]">
                  {allItems.map((item) => (
                    <tr
                      key={item.id}
                      className="hover:bg-[var(--bg-surface)] transition-colors"
                    >
                      <td className="px-6 py-4">
                        <input
                          type="checkbox"
                          checked={selectedItems.has(item.id)}
                          onChange={(e) => {
                            const checked = e.target.checked;
                            setSelectedItems((prev) => {
                              const next = new Set(prev);
                              if (checked) {
                                next.add(item.id);
                              } else {
                                next.delete(item.id);
                              }
                              return next;
                            });
                          }}
                          className="w-4 h-4 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
                        />
                      </td>
                      <td className="px-6 py-4">
                        {item.thumbnail ? (
                          <img
                            src={item.thumbnail}
                            alt={item.name}
                            className="h-16 w-28 rounded border border-[var(--border-base)] object-cover"
                          />
                        ) : (
                          <div className="h-16 w-28 rounded border border-[var(--border-base)] bg-[var(--bg-surface)] flex items-center justify-center">
                            {item.type === "image" ? (
                              <ImageIcon className="h-6 w-6 text-[var(--text-muted)]" />
                            ) : (
                              <Video className="h-6 w-6 text-[var(--text-muted)]" />
                            )}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sm font-medium text-[var(--text-primary)] hover:text-[var(--accent-primary)] transition-colors"
                        >
                          {item.name}
                        </a>
                      </td>
                      <td className="px-6 py-4">
                        <StatusChip status="info" label={item.type} />
                      </td>
                      <td className="px-6 py-4 text-sm text-[var(--text-secondary)]">
                        {item.size ? formatBytes(item.size) : "—"}
                      </td>
                      <td className="px-6 py-4 text-sm text-[var(--text-muted)]">
                        {item.created
                          ? new Date(item.created).toLocaleDateString()
                          : "—"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <a href={item.url} download>
                            <SecondaryButton
                              size="sm"
                              icon={<Download className="h-3 w-3" />}
                            >
                              Download
                            </SecondaryButton>
                          </a>
                          <IconButton
                            icon={<Trash2 className="h-4 w-4" />}
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDelete(item.id, item.type)}
                            disabled={isDeleting === item.id}
                            aria-label="Delete"
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

          {allItems.length > 0 && (
            <div className="mt-6 flex justify-center">
              <SecondaryButton
                onClick={loadMore}
                disabled={!hasMore && images.length + videos.length >= total}
              >
                Load More
              </SecondaryButton>
            </div>
          )}
        </SectionCard>
      </main>
    </div>
  );
}
