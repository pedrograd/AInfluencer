"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import {
  PageHeader,
  SectionCard,
  SecondaryButton,
  Input,
  Select,
  MetricCard,
  LoadingSkeleton,
  ErrorBanner,
  EmptyState,
} from "@/components/ui";
import { Home, BarChart3, TrendingUp, Users, Heart, Eye } from "lucide-react";

type AnalyticsOverview = {
  total_posts: number;
  total_engagement: number;
  total_followers: number;
  total_reach: number;
  engagement_rate: number;
  follower_growth: number;
  top_performing_posts: Array<{
    post_id: string;
    character_id: string;
    platform: string;
    total_engagement: number;
    engagement_rate: number;
    published_at: string | null;
    platform_post_url: string | null;
  }>;
  platform_breakdown: Record<
    string,
    {
      posts: number;
      engagement: number;
      followers: number;
      reach: number;
    }
  >;
  trends: Record<string, number[]>;
};

type Character = {
  id: string;
  name: string;
  status: string;
};

type CharactersResponse = {
  success: boolean;
  data: {
    characters: Character[];
    total: number;
  };
};

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedCharacter, setSelectedCharacter] = useState<string>("");
  const [selectedPlatform, setSelectedPlatform] = useState<string>("");
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");

  const fetchCharacters = async () => {
    try {
      const response = await apiGet<CharactersResponse>(
        "/api/characters?limit=100&offset=0"
      );
      if (response.success) {
        setCharacters(response.data.characters);
      }
    } catch (err) {
      console.error("Failed to load characters:", err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      if (selectedCharacter) {
        params.append("character_id", selectedCharacter);
      }
      if (selectedPlatform) {
        params.append("platform", selectedPlatform);
      }
      if (fromDate) {
        params.append("from_date", fromDate);
      }
      if (toDate) {
        params.append("to_date", toDate);
      }

      const data = await apiGet<AnalyticsOverview>(
        `/api/analytics/overview${
          params.toString() ? `?${params.toString()}` : ""
        }`
      );
      setOverview(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharacters();
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [selectedCharacter, selectedPlatform, fromDate, toDate]);

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const formatPercentage = (rate: number) => {
    return `${(rate * 100).toFixed(2)}%`;
  };

  const platforms = overview ? Object.keys(overview.platform_breakdown) : [];

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        <PageHeader
          title="Analytics Dashboard"
          description="Track performance metrics and engagement across all platforms"
          action={
            <Link href="/">
              <SecondaryButton size="sm" icon={<Home className="h-4 w-4" />}>
                Home
              </SecondaryButton>
            </Link>
          }
        />

        {/* Filters */}
        <SectionCard title="Filters" className="mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Select
              label="Character"
              options={[
                { value: "", label: "All Characters" },
                ...characters.map((char) => ({
                  value: char.id,
                  label: char.name,
                })),
              ]}
              value={selectedCharacter}
              onChange={(e) => setSelectedCharacter(e.target.value)}
            />
            <Select
              label="Platform"
              options={[
                { value: "", label: "All Platforms" },
                ...platforms.map((platform) => ({
                  value: platform,
                  label: platform.charAt(0).toUpperCase() + platform.slice(1),
                })),
              ]}
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
            />
            <Input
              label="From Date"
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
            />
            <Input
              label="To Date"
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
            />
          </div>
        </SectionCard>

        {error && (
          <div className="mb-6">
            <ErrorBanner
              title="Error loading analytics"
              message={error}
              remediation={{
                label: "Retry",
                onClick: fetchAnalytics,
              }}
            />
          </div>
        )}

        {loading && !overview ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <LoadingSkeleton key={i} variant="card" height="120px" />
              ))}
            </div>
          </div>
        ) : overview ? (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <MetricCard
                label="Total Posts"
                value={formatNumber(overview.total_posts)}
                icon={<BarChart3 className="h-5 w-5" />}
                variant="icon"
              />
              <MetricCard
                label="Total Engagement"
                value={formatNumber(overview.total_engagement)}
                icon={<Heart className="h-5 w-5" />}
                variant="icon"
              />
              <MetricCard
                label="Total Followers"
                value={formatNumber(overview.total_followers)}
                icon={<Users className="h-5 w-5" />}
                variant="icon"
              />
              <MetricCard
                label="Engagement Rate"
                value={formatPercentage(overview.engagement_rate)}
                icon={<TrendingUp className="h-5 w-5" />}
                variant="icon"
              />
            </div>

            {/* Additional Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <MetricCard
                label="Total Reach"
                value={formatNumber(overview.total_reach)}
                icon={<Eye className="h-5 w-5" />}
                variant="icon"
              />
              <MetricCard
                label="Follower Growth"
                value={`${
                  overview.follower_growth >= 0 ? "+" : ""
                }${formatNumber(overview.follower_growth)}`}
                icon={<TrendingUp className="h-5 w-5" />}
                variant="icon"
              />
              <MetricCard
                label="Average Engagement"
                value={
                  overview.total_posts > 0
                    ? formatNumber(
                        overview.total_engagement / overview.total_posts
                      )
                    : "0"
                }
                icon={<Heart className="h-5 w-5" />}
                variant="icon"
              />
            </div>

            {/* Platform Breakdown */}
            {platforms.length > 0 && (
              <SectionCard title="Platform Breakdown" className="mb-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {platforms.map((platform) => {
                    const data = overview.platform_breakdown[platform];
                    return (
                      <div
                        key={platform}
                        className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] p-4"
                      >
                        <div className="text-sm font-semibold text-[var(--text-primary)] mb-3 capitalize">
                          {platform}
                        </div>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-[var(--text-secondary)]">
                              Posts:
                            </span>
                            <span className="text-[var(--text-primary)] font-medium">
                              {formatNumber(data.posts)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[var(--text-secondary)]">
                              Engagement:
                            </span>
                            <span className="text-[var(--accent-primary)] font-medium">
                              {formatNumber(data.engagement)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[var(--text-secondary)]">
                              Followers:
                            </span>
                            <span className="text-[var(--success)] font-medium">
                              {formatNumber(data.followers)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[var(--text-secondary)]">
                              Reach:
                            </span>
                            <span className="text-[var(--text-primary)] font-medium">
                              {formatNumber(data.reach)}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </SectionCard>
            )}

            {/* Top Performing Posts */}
            {overview.top_performing_posts.length > 0 && (
              <SectionCard title="Top Performing Posts" className="mb-6">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs text-[var(--text-secondary)] border-b border-[var(--border-base)]">
                      <tr>
                        <th className="px-6 py-3 uppercase tracking-wider">
                          Platform
                        </th>
                        <th className="px-6 py-3 uppercase tracking-wider">
                          Engagement
                        </th>
                        <th className="px-6 py-3 uppercase tracking-wider">
                          Engagement Rate
                        </th>
                        <th className="px-6 py-3 uppercase tracking-wider">
                          Published
                        </th>
                        <th className="px-6 py-3 uppercase tracking-wider">
                          Link
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border-base)]">
                      {overview.top_performing_posts.map((post) => (
                        <tr
                          key={post.post_id}
                          className="hover:bg-[var(--bg-surface)] transition-colors"
                        >
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm font-medium text-[var(--text-primary)] capitalize">
                              {post.platform}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-[var(--accent-primary)] font-medium">
                              {formatNumber(post.total_engagement)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-[var(--warning)] font-medium">
                              {formatPercentage(post.engagement_rate)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-muted)]">
                            {post.published_at
                              ? new Date(post.published_at).toLocaleDateString()
                              : "N/A"}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {post.platform_post_url ? (
                              <a
                                href={post.platform_post_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-[var(--accent-primary)] hover:text-[var(--accent-primary-hover)] transition-colors"
                              >
                                View →
                              </a>
                            ) : (
                              <span className="text-sm text-[var(--text-muted)]">
                                N/A
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </SectionCard>
            )}

            {/* Trends Visualization */}
            {Object.keys(overview.trends).length > 0 && (
              <SectionCard title="Trends" className="mb-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(overview.trends).map(([key, values]) => (
                    <div
                      key={key}
                      className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] p-4"
                    >
                      <div className="text-sm font-semibold text-[var(--text-primary)] mb-4 capitalize">
                        {key.replace(/_/g, " ")}
                      </div>
                      <div className="h-32 flex items-end gap-1">
                        {values.map((value, idx) => {
                          const maxValue = Math.max(...values, 1);
                          const height = (value / maxValue) * 100;
                          return (
                            <div
                              key={idx}
                              className="flex-1 bg-[var(--accent-primary)] rounded-t transition-all hover:bg-[var(--accent-primary-hover)]"
                              style={{ height: `${height}%` }}
                              title={`${value}`}
                            />
                          );
                        })}
                      </div>
                      <div className="mt-2 text-xs text-[var(--text-muted)] text-center">
                        {values.length} data points
                      </div>
                    </div>
                  ))}
                </div>
              </SectionCard>
            )}

            {/* Empty State */}
            {overview.total_posts === 0 && (
              <EmptyState
                icon={<BarChart3 className="h-12 w-12" />}
                title="No Analytics Data"
                description="No analytics data available for the selected filters."
                action={{
                  label: "Refresh",
                  onClick: fetchAnalytics,
                }}
              />
            )}
          </>
        ) : null}
      </main>
    </div>
  );
}
