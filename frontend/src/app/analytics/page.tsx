"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

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
      const response = await apiGet<CharactersResponse>("/api/characters?limit=100&offset=0");
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
        `/api/analytics/overview${params.toString() ? `?${params.toString()}` : ""}`
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

  const platforms = overview
    ? Object.keys(overview.platform_breakdown)
    : [];

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold mb-2">Analytics Dashboard</h1>
            <p className="text-slate-400">
              Track performance metrics and engagement across all platforms
            </p>
          </div>
          <Link
            href="/"
            className="px-4 py-2 text-slate-400 hover:text-slate-100 transition-colors"
          >
            ← Back to Dashboard
          </Link>
        </div>

        {/* Filters */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Character
            </label>
            <select
              value={selectedCharacter}
              onChange={(e) => setSelectedCharacter(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Characters</option>
              {characters.map((char) => (
                <option key={char.id} value={char.id}>
                  {char.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Platform
            </label>
            <select
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Platforms</option>
              {platforms.map((platform) => (
                <option key={platform} value={platform}>
                  {platform.charAt(0).toUpperCase() + platform.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              From Date
            </label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              To Date
            </label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
            <p className="mt-4 text-slate-400">Loading analytics...</p>
          </div>
        )}

        {/* Analytics Content */}
        {!loading && overview && (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">Total Posts</div>
                <div className="text-3xl font-bold text-slate-100">
                  {formatNumber(overview.total_posts)}
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">Total Engagement</div>
                <div className="text-3xl font-bold text-indigo-400">
                  {formatNumber(overview.total_engagement)}
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">Total Followers</div>
                <div className="text-3xl font-bold text-green-400">
                  {formatNumber(overview.total_followers)}
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">Engagement Rate</div>
                <div className="text-3xl font-bold text-yellow-400">
                  {formatPercentage(overview.engagement_rate)}
                </div>
              </div>
            </div>

            {/* Additional Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">Total Reach</div>
                <div className="text-2xl font-bold text-slate-100">
                  {formatNumber(overview.total_reach)}
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">Follower Growth</div>
                <div className="text-2xl font-bold text-green-400">
                  {overview.follower_growth >= 0 ? "+" : ""}
                  {formatNumber(overview.follower_growth)}
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">Average Engagement</div>
                <div className="text-2xl font-bold text-indigo-400">
                  {overview.total_posts > 0
                    ? formatNumber(overview.total_engagement / overview.total_posts)
                    : "0"}
                </div>
              </div>
            </div>

            {/* Platform Breakdown */}
            {platforms.length > 0 && (
              <div className="mb-8">
                <h2 className="text-2xl font-bold mb-4">Platform Breakdown</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {platforms.map((platform) => {
                    const data = overview.platform_breakdown[platform];
                    return (
                      <div
                        key={platform}
                        className="bg-slate-800 border border-slate-700 rounded-lg p-6"
                      >
                        <div className="text-lg font-semibold mb-4 capitalize">
                          {platform}
                        </div>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-slate-400">Posts:</span>
                            <span className="text-slate-100 font-medium">
                              {formatNumber(data.posts)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Engagement:</span>
                            <span className="text-indigo-400 font-medium">
                              {formatNumber(data.engagement)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Followers:</span>
                            <span className="text-green-400 font-medium">
                              {formatNumber(data.followers)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Reach:</span>
                            <span className="text-slate-100 font-medium">
                              {formatNumber(data.reach)}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Top Performing Posts */}
            {overview.top_performing_posts.length > 0 && (
              <div className="mb-8">
                <h2 className="text-2xl font-bold mb-4">Top Performing Posts</h2>
                <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-slate-700/50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                          Platform
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                          Engagement
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                          Engagement Rate
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                          Published
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                          Link
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {overview.top_performing_posts.map((post) => (
                        <tr key={post.post_id} className="hover:bg-slate-700/30">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm font-medium text-slate-100 capitalize">
                              {post.platform}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-indigo-400 font-medium">
                              {formatNumber(post.total_engagement)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-yellow-400 font-medium">
                              {formatPercentage(post.engagement_rate)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
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
                                className="text-sm text-indigo-400 hover:text-indigo-300"
                              >
                                View →
                              </a>
                            ) : (
                              <span className="text-sm text-slate-500">N/A</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Trends Visualization */}
            {Object.keys(overview.trends).length > 0 && (
              <div>
                <h2 className="text-2xl font-bold mb-4">Trends</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {Object.entries(overview.trends).map(([key, values]) => (
                    <div
                      key={key}
                      className="bg-slate-800 border border-slate-700 rounded-lg p-6"
                    >
                      <div className="text-lg font-semibold mb-4 capitalize">
                        {key.replace(/_/g, " ")}
                      </div>
                      <div className="h-32 flex items-end gap-1">
                        {values.map((value, idx) => {
                          const maxValue = Math.max(...values, 1);
                          const height = (value / maxValue) * 100;
                          return (
                            <div
                              key={idx}
                              className="flex-1 bg-indigo-500 rounded-t"
                              style={{ height: `${height}%` }}
                              title={`${value}`}
                            />
                          );
                        })}
                      </div>
                      <div className="mt-2 text-xs text-slate-400 text-center">
                        {values.length} data points
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Empty State */}
        {!loading && !error && overview && overview.total_posts === 0 && (
          <div className="text-center py-12">
            <p className="text-slate-400 text-lg">
              No analytics data available for the selected filters.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
