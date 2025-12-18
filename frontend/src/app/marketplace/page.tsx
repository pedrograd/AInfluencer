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
  ErrorBanner,
  Alert,
} from "@/components/ui";
import {
  Home,
  Grid3x3,
  List,
  Star,
  Users,
  Sparkles,
  Search,
  CheckCircle2,
} from "lucide-react";

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
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

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

  const handleUseTemplate = async (
    templateId: string,
    templateName: string
  ) => {
    if (
      !confirm(
        `Create a new character from template "${templateName}"? This will copy all personality and appearance settings.`
      )
    ) {
      return;
    }

    try {
      setActionLoading(templateId);
      setError(null);
      const response = await useTemplate(templateId, {
        template_id: templateId,
      });
      if (response.success) {
        setSuccessMessage(
          "Character created successfully! Redirecting to characters page..."
        );
        setTimeout(() => {
          router.push("/characters");
        }, 1500);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create character from template"
      );
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
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        <PageHeader
          title="Character Template Marketplace"
          description="Browse and use pre-configured character templates"
          action={
            <div className="flex gap-2">
              <Link href="/characters">
                <SecondaryButton size="sm" icon={<Home className="h-4 w-4" />}>
                  My Characters
                </SecondaryButton>
              </Link>
              <IconButton
                icon={
                  viewMode === "grid" ? (
                    <List className="h-4 w-4" />
                  ) : (
                    <Grid3x3 className="h-4 w-4" />
                  )
                }
                size="md"
                variant="ghost"
                onClick={() =>
                  setViewMode(viewMode === "grid" ? "list" : "grid")
                }
                aria-label={`Switch to ${
                  viewMode === "grid" ? "list" : "grid"
                } view`}
              />
            </div>
          }
        />

        {/* Filters */}
        <SectionCard title="Filters" className="mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search templates..."
                icon={<Search className="h-4 w-4" />}
              />
            </div>
            <Select
              options={categories.map((cat) => ({
                value: cat,
                label:
                  cat === "all"
                    ? "All Categories"
                    : cat.charAt(0).toUpperCase() + cat.slice(1),
              }))}
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full sm:w-48"
            />
            <label className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] cursor-pointer hover:bg-[var(--bg-surface)] transition-colors">
              <input
                type="checkbox"
                checked={featuredOnly}
                onChange={(e) => setFeaturedOnly(e.target.checked)}
                className="w-4 h-4 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
              />
              <span className="text-sm text-[var(--text-primary)]">
                Featured Only
              </span>
            </label>
          </div>
        </SectionCard>

        {error && (
          <div className="mb-6">
            <ErrorBanner
              title="Error loading templates"
              message={error}
              remediation={{
                label: "Retry",
                onClick: fetchTemplates,
              }}
            />
          </div>
        )}

        {successMessage && (
          <div className="mb-6">
            <Alert
              message={successMessage}
              variant="success"
              dismissible
              onDismiss={() => setSuccessMessage(null)}
            />
          </div>
        )}

        <SectionCard
          title={`${pagination.total} Template(s)`}
          description={
            pagination.total > 0
              ? `Showing ${pagination.offset + 1}-${Math.min(
                  pagination.offset + pagination.limit,
                  pagination.total
                )} of ${pagination.total}`
              : undefined
          }
          loading={loading}
          empty={!loading && templates.length === 0}
          emptyMessage="No templates found. Try adjusting your search or filters."
        >
          {!loading && templates.length > 0 && (
            <>
              {viewMode === "grid" ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
                  {templates.map((template) => (
                    <div
                      key={template.id}
                      className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] p-4 sm:p-6 hover:border-[var(--accent-primary)] transition-all hover:shadow-md"
                    >
                      {template.is_featured && (
                        <div className="mb-2">
                          <StatusChip
                            status="warning"
                            label={
                              <span className="flex items-center gap-1">
                                <Star className="h-3 w-3 fill-current" />
                                Featured
                              </span>
                            }
                            className="text-[10px]"
                          />
                        </div>
                      )}
                      {template.preview_image_url ? (
                        <img
                          src={template.preview_image_url}
                          alt={template.name}
                          className="w-full h-48 object-cover rounded-lg mb-4"
                        />
                      ) : (
                        <div className="w-full h-48 bg-[var(--bg-surface)] rounded-lg mb-4 flex items-center justify-center">
                          <Sparkles className="h-12 w-12 text-[var(--text-muted)]" />
                        </div>
                      )}
                      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                        {template.name}
                      </h3>
                      {template.description && (
                        <p className="text-[var(--text-secondary)] text-sm mb-4 line-clamp-2">
                          {template.description}
                        </p>
                      )}
                      <div className="flex flex-wrap gap-2 mb-4">
                        {template.category && (
                          <StatusChip
                            status="info"
                            label={template.category}
                            className="text-[10px]"
                          />
                        )}
                        {template.tags?.slice(0, 2).map((tag, idx) => (
                          <StatusChip
                            key={idx}
                            status="info"
                            label={tag}
                            className="text-[10px]"
                          />
                        ))}
                      </div>
                      <div className="flex items-center justify-between text-sm text-[var(--text-secondary)] mb-4">
                        <span className="flex items-center gap-1">
                          <Users className="h-4 w-4" />
                          {template.download_count} uses
                        </span>
                        {template.rating && (
                          <span className="flex items-center gap-1">
                            <Star className="h-4 w-4 fill-current text-[var(--warning)]" />
                            {template.rating.toFixed(1)}
                          </span>
                        )}
                      </div>
                      <PrimaryButton
                        onClick={() =>
                          handleUseTemplate(template.id, template.name)
                        }
                        disabled={actionLoading === template.id}
                        loading={actionLoading === template.id}
                        icon={<Sparkles className="h-4 w-4" />}
                        className="w-full"
                      >
                        Use Template
                      </PrimaryButton>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {templates.map((template) => (
                    <div
                      key={template.id}
                      className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] p-4 sm:p-6 hover:border-[var(--accent-primary)] transition-all"
                    >
                      <div className="flex flex-col sm:flex-row gap-4">
                        {template.preview_image_url ? (
                          <img
                            src={template.preview_image_url}
                            alt={template.name}
                            className="w-full sm:w-32 h-32 object-cover rounded-lg"
                          />
                        ) : (
                          <div className="w-full sm:w-32 h-32 bg-[var(--bg-surface)] rounded-lg flex items-center justify-center">
                            <Sparkles className="h-12 w-12 text-[var(--text-muted)]" />
                          </div>
                        )}
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
                                {template.name}
                              </h3>
                              {template.description && (
                                <p className="text-[var(--text-secondary)] text-sm mb-2">
                                  {template.description}
                                </p>
                              )}
                            </div>
                            {template.is_featured && (
                              <StatusChip
                                status="warning"
                                label={
                                  <span className="flex items-center gap-1">
                                    <Star className="h-3 w-3 fill-current" />
                                    Featured
                                  </span>
                                }
                                className="text-[10px]"
                              />
                            )}
                          </div>
                          <div className="flex flex-wrap gap-2 mb-3">
                            {template.category && (
                              <StatusChip
                                status="info"
                                label={template.category}
                                className="text-[10px]"
                              />
                            )}
                            {template.tags?.map((tag, idx) => (
                              <StatusChip
                                key={idx}
                                status="info"
                                label={tag}
                                className="text-[10px]"
                              />
                            ))}
                          </div>
                          <div className="flex items-center gap-4 text-sm text-[var(--text-secondary)] mb-3">
                            <span className="flex items-center gap-1">
                              <Users className="h-4 w-4" />
                              {template.download_count} uses
                            </span>
                            {template.rating && (
                              <span className="flex items-center gap-1">
                                <Star className="h-4 w-4 fill-current text-[var(--warning)]" />
                                {template.rating.toFixed(1)} (
                                {template.rating_count} ratings)
                              </span>
                            )}
                            {template.creator_name && (
                              <span>by {template.creator_name}</span>
                            )}
                          </div>
                          <PrimaryButton
                            onClick={() =>
                              handleUseTemplate(template.id, template.name)
                            }
                            disabled={actionLoading === template.id}
                            loading={actionLoading === template.id}
                            icon={<Sparkles className="h-4 w-4" />}
                          >
                            Use Template
                          </PrimaryButton>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Pagination */}
              {pagination.total > pagination.limit && (
                <div className="mt-6 flex items-center justify-center gap-4">
                  <SecondaryButton
                    onClick={() =>
                      setPagination((prev) => ({
                        ...prev,
                        offset: Math.max(0, prev.offset - prev.limit),
                      }))
                    }
                    disabled={pagination.offset === 0}
                  >
                    Previous
                  </SecondaryButton>
                  <span className="text-sm text-[var(--text-secondary)]">
                    Showing {pagination.offset + 1}-
                    {Math.min(
                      pagination.offset + pagination.limit,
                      pagination.total
                    )}{" "}
                    of {pagination.total}
                  </span>
                  <SecondaryButton
                    onClick={() =>
                      setPagination((prev) => ({
                        ...prev,
                        offset: prev.offset + prev.limit,
                      }))
                    }
                    disabled={!pagination.has_more}
                  >
                    Next
                  </SecondaryButton>
                </div>
              )}
            </>
          )}
        </SectionCard>
      </main>
    </div>
  );
}
