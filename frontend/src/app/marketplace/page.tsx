"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  listTemplates,
  getTemplate,
  useTemplate,
  type CharacterTemplate,
  type TemplateListResponse,
} from "@/lib/api";

type ViewMode = "grid" | "list";

export default function MarketplacePage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<CharacterTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [featuredOnly, setFeaturedOnly] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 20,
    offset: 0,
    has_more: false,
  });
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await listTemplates({
        category: categoryFilter !== "all" ? categoryFilter : undefined,
        search: search || undefined,
        featured_only: featuredOnly || undefined,
        limit: pagination.limit,
        offset: pagination.offset,
      });
      if (response.success) {
        setTemplates(response.data);
        setPagination(response.pagination);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load templates");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, [search, categoryFilter, featuredOnly, pagination.offset]);

  const handleUseTemplate = async (templateId: string, templateName: string) => {
    if (
      !confirm(
        `Create a new character from template "${templateName}"? This will copy all personality and appearance settings.`
      )
    ) {
      return;
    }

    try {
      setActionLoading(templateId);
      const response = await useTemplate(templateId, { template_id: templateId });
      if (response.success) {
        alert("Character created successfully! Redirecting to characters page...");
        router.push("/characters");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create character from template");
    } finally {
      setActionLoading(null);
    }
  };

  const categories = [
    "all",
    "influencer",
    "professional",
    "creative",
    "entertainer",
    "authentic",
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white p-4 sm:p-6 lg:p-10">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-2 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                Character Template Marketplace
              </h1>
              <p className="text-gray-400 text-sm sm:text-base">
                Browse and use pre-configured character templates
              </p>
            </div>
            <Link
              href="/characters"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors text-sm sm:text-base"
            >
              My Characters
            </Link>
          </div>

          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search templates..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-gray-500"
              />
            </div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat === "all" ? "All Categories" : cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg cursor-pointer hover:bg-gray-750">
              <input
                type="checkbox"
                checked={featuredOnly}
                onChange={(e) => setFeaturedOnly(e.target.checked)}
                className="w-4 h-4 text-indigo-600 bg-gray-700 border-gray-600 rounded focus:ring-indigo-500"
              />
              <span className="text-sm">Featured Only</span>
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode("grid")}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  viewMode === "grid"
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                }`}
              >
                Grid
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  viewMode === "list"
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                }`}
              >
                List
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-400"></div>
            <p className="mt-4 text-gray-400">Loading templates...</p>
          </div>
        )}

        {/* Templates Grid/List */}
        {!loading && templates.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">No templates found</p>
            <p className="text-gray-500 text-sm mt-2">
              Try adjusting your search or filters
            </p>
          </div>
        )}

        {!loading && templates.length > 0 && (
          <>
            {viewMode === "grid" ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 sm:p-6 hover:border-indigo-500/50 transition-all hover:shadow-lg hover:shadow-indigo-500/10"
                  >
                    {template.is_featured && (
                      <div className="mb-2">
                        <span className="inline-block px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded border border-yellow-500/30">
                          ⭐ Featured
                        </span>
                      </div>
                    )}
                    {template.preview_image_url ? (
                      <img
                        src={template.preview_image_url}
                        alt={template.name}
                        className="w-full h-48 object-cover rounded-lg mb-4"
                      />
                    ) : (
                      <div className="w-full h-48 bg-gray-700 rounded-lg mb-4 flex items-center justify-center">
                        <span className="text-gray-500 text-4xl">👤</span>
                      </div>
                    )}
                    <h3 className="text-lg font-semibold mb-2">{template.name}</h3>
                    {template.description && (
                      <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                        {template.description}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {template.category && (
                        <span className="px-2 py-1 bg-indigo-500/20 text-indigo-400 text-xs rounded">
                          {template.category}
                        </span>
                      )}
                      {template.tags?.slice(0, 2).map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
                      <span>👥 {template.download_count} uses</span>
                      {template.rating && (
                        <span>⭐ {template.rating.toFixed(1)}</span>
                      )}
                    </div>
                    <button
                      onClick={() => handleUseTemplate(template.id, template.name)}
                      disabled={actionLoading === template.id}
                      className="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {actionLoading === template.id ? "Creating..." : "Use Template"}
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 sm:p-6 hover:border-indigo-500/50 transition-all"
                  >
                    <div className="flex flex-col sm:flex-row gap-4">
                      {template.preview_image_url ? (
                        <img
                          src={template.preview_image_url}
                          alt={template.name}
                          className="w-full sm:w-32 h-32 object-cover rounded-lg"
                        />
                      ) : (
                        <div className="w-full sm:w-32 h-32 bg-gray-700 rounded-lg flex items-center justify-center">
                          <span className="text-gray-500 text-4xl">👤</span>
                        </div>
                      )}
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h3 className="text-lg font-semibold mb-1">{template.name}</h3>
                            {template.description && (
                              <p className="text-gray-400 text-sm mb-2">{template.description}</p>
                            )}
                          </div>
                          {template.is_featured && (
                            <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded border border-yellow-500/30">
                              ⭐ Featured
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-2 mb-3">
                          {template.category && (
                            <span className="px-2 py-1 bg-indigo-500/20 text-indigo-400 text-xs rounded">
                              {template.category}
                            </span>
                          )}
                          {template.tags?.map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-400 mb-3">
                          <span>👥 {template.download_count} uses</span>
                          {template.rating && (
                            <span>⭐ {template.rating.toFixed(1)} ({template.rating_count} ratings)</span>
                          )}
                          {template.creator_name && (
                            <span>by {template.creator_name}</span>
                          )}
                        </div>
                        <button
                          onClick={() => handleUseTemplate(template.id, template.name)}
                          disabled={actionLoading === template.id}
                          className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {actionLoading === template.id ? "Creating..." : "Use Template"}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {pagination.total > pagination.limit && (
              <div className="mt-6 flex items-center justify-center gap-4">
                <button
                  onClick={() =>
                    setPagination((prev) => ({
                      ...prev,
                      offset: Math.max(0, prev.offset - prev.limit),
                    }))
                  }
                  disabled={pagination.offset === 0}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-gray-400">
                  Showing {pagination.offset + 1}-
                  {Math.min(pagination.offset + pagination.limit, pagination.total)} of{" "}
                  {pagination.total}
                </span>
                <button
                  onClick={() =>
                    setPagination((prev) => ({
                      ...prev,
                      offset: prev.offset + prev.limit,
                    }))
                  }
                  disabled={!pagination.has_more}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
