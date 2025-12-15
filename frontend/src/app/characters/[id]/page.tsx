"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

type Character = {
  id: string;
  name: string;
  bio: string | null;
  age: number | null;
  location: string | null;
  timezone: string;
  interests: string[] | null;
  profile_image_url: string | null;
  profile_image_path: string | null;
  status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  personality?: {
    extroversion: number | null;
    creativity: number | null;
    humor: number | null;
    professionalism: number | null;
    authenticity: number | null;
    communication_style: string | null;
    preferred_topics: string[] | null;
    content_tone: string | null;
    llm_personality_prompt: string | null;
    temperature: number | null;
  };
  appearance?: {
    face_reference_image_url: string | null;
    face_reference_image_path: string | null;
    face_consistency_method: string;
    lora_model_path: string | null;
    hair_color: string | null;
    hair_style: string | null;
    eye_color: string | null;
    skin_tone: string | null;
    body_type: string | null;
    height: string | null;
    age_range: string | null;
    clothing_style: string | null;
    preferred_colors: string[] | null;
    style_keywords: string[] | null;
    base_model: string;
    negative_prompt: string | null;
    default_prompt_prefix: string | null;
  };
};

type CharacterResponse = {
  success: boolean;
  data: Character;
};

type ContentItem = {
  id: string;
  character_id: string;
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

export default function CharacterDetailPage() {
  const params = useParams();
  const characterId = params.id as string;
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "content" | "activity">("overview");
  const [contentItems, setContentItems] = useState<ContentItem[]>([]);
  const [contentLoading, setContentLoading] = useState(false);
  const [contentError, setContentError] = useState<string | null>(null);
  const [contentTotal, setContentTotal] = useState(0);

  useEffect(() => {
    const fetchCharacter = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiGet<CharacterResponse>(`/api/characters/${characterId}`);
        if (response.success) {
          setCharacter(response.data);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load character");
      } finally {
        setLoading(false);
      }
    };

    if (characterId) {
      fetchCharacter();
    }
  }, [characterId]);

  useEffect(() => {
    const fetchContent = async () => {
      if (activeTab !== "content" || !characterId) return;
      
      try {
        setContentLoading(true);
        setContentError(null);
        const params = new URLSearchParams({
          character_id: characterId,
          limit: "50",
          offset: "0",
        });
        const response = await apiGet<ContentLibraryResponse>(`/api/content/library?${params.toString()}`);
        if (response.ok) {
          setContentItems(response.items || []);
          setContentTotal(response.total || 0);
        } else {
          setContentError(response.error || "Failed to load content");
        }
      } catch (err) {
        setContentError(err instanceof Error ? err.message : "Failed to load content");
      } finally {
        setContentLoading(false);
      }
    };

    fetchContent();
  }, [activeTab, characterId]);

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

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
            <p className="mt-4 text-slate-400">Loading character...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !character) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 p-8">
        <div className="max-w-7xl mx-auto">
          <Link
            href="/characters"
            className="text-indigo-400 hover:text-indigo-300 mb-4 inline-block"
          >
            ← Back to Characters
          </Link>
          <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-6">
            <p className="text-red-400">Error: {error || "Character not found"}</p>
            <Link
              href="/characters"
              className="mt-4 inline-block px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              Go Back
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/characters"
            className="text-indigo-400 hover:text-indigo-300 mb-4 inline-block"
          >
            ← Back to Characters
          </Link>
          <div className="flex items-center justify-between">
            <h1 className="text-4xl font-bold">{character.name}</h1>
            <div className="flex gap-3">
              <Link
                href={`/characters/${characterId}/edit`}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
              >
                Edit
              </Link>
              <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-colors">
                Settings
              </button>
            </div>
          </div>
        </div>

        {/* Character Header Card */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-6">
            {/* Avatar */}
            <div className="flex-shrink-0">
              {character.profile_image_url ? (
                <img
                  src={character.profile_image_url}
                  alt={character.name}
                  className="w-32 h-32 rounded-lg object-cover"
                />
              ) : (
                <div className="w-32 h-32 bg-slate-700 rounded-lg flex items-center justify-center">
                  <span className="text-4xl text-slate-500">
                    {character.name.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
            </div>

            {/* Character Info */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <span
                  className={`px-3 py-1 rounded text-sm font-medium border ${getStatusColor(
                    character.status
                  )}`}
                >
                  {character.status}
                </span>
                <span className="text-sm text-slate-400">
                  Created: {new Date(character.created_at).toLocaleDateString()}
                </span>
              </div>
              {character.bio && (
                <p className="text-slate-300 mb-4">{character.bio}</p>
              )}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                {character.age && (
                  <div>
                    <span className="text-slate-400">Age:</span>{" "}
                    <span className="text-slate-200">{character.age}</span>
                  </div>
                )}
                {character.location && (
                  <div>
                    <span className="text-slate-400">Location:</span>{" "}
                    <span className="text-slate-200">{character.location}</span>
                  </div>
                )}
                <div>
                  <span className="text-slate-400">Timezone:</span>{" "}
                  <span className="text-slate-200">{character.timezone}</span>
                </div>
                <div>
                  <span className="text-slate-400">Active:</span>{" "}
                  <span className={character.is_active ? "text-green-400" : "text-red-400"}>
                    {character.is_active ? "Yes" : "No"}
                  </span>
                </div>
              </div>
              {character.interests && character.interests.length > 0 && (
                <div className="mt-4">
                  <span className="text-slate-400 text-sm">Interests: </span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {character.interests.map((interest, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-slate-700 text-slate-300 rounded text-sm"
                      >
                        {interest}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-slate-700 mb-6">
          <div className="flex gap-6">
            <button
              onClick={() => setActiveTab("overview")}
              className={`pb-3 px-1 font-medium transition-colors ${
                activeTab === "overview"
                  ? "text-indigo-400 border-b-2 border-indigo-400"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab("content")}
              className={`pb-3 px-1 font-medium transition-colors ${
                activeTab === "content"
                  ? "text-indigo-400 border-b-2 border-indigo-400"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              Content
            </button>
            <button
              onClick={() => setActiveTab("activity")}
              className={`pb-3 px-1 font-medium transition-colors ${
                activeTab === "activity"
                  ? "text-indigo-400 border-b-2 border-indigo-400"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              Activity
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          {activeTab === "overview" && (
            <div>
              <h2 className="text-2xl font-semibold mb-6">Overview</h2>
              
              {/* Personality Section */}
              {character.personality && (
                <div className="mb-6">
                  <h3 className="text-xl font-semibold mb-4">Personality Traits</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {character.personality.extroversion !== null && (
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-slate-400">Extroversion</span>
                          <span className="text-slate-300">
                            {Math.round(character.personality.extroversion * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-indigo-500 h-2 rounded-full"
                            style={{
                              width: `${character.personality.extroversion * 100}%`,
                            }}
                          ></div>
                        </div>
                      </div>
                    )}
                    {character.personality.creativity !== null && (
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-slate-400">Creativity</span>
                          <span className="text-slate-300">
                            {Math.round(character.personality.creativity * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-indigo-500 h-2 rounded-full"
                            style={{
                              width: `${character.personality.creativity * 100}%`,
                            }}
                          ></div>
                        </div>
                      </div>
                    )}
                    {character.personality.humor !== null && (
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-slate-400">Humor</span>
                          <span className="text-slate-300">
                            {Math.round(character.personality.humor * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-indigo-500 h-2 rounded-full"
                            style={{
                              width: `${character.personality.humor * 100}%`,
                            }}
                          ></div>
                        </div>
                      </div>
                    )}
                    {character.personality.professionalism !== null && (
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-slate-400">Professionalism</span>
                          <span className="text-slate-300">
                            {Math.round(character.personality.professionalism * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-indigo-500 h-2 rounded-full"
                            style={{
                              width: `${character.personality.professionalism * 100}%`,
                            }}
                          ></div>
                        </div>
                      </div>
                    )}
                    {character.personality.authenticity !== null && (
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-slate-400">Authenticity</span>
                          <span className="text-slate-300">
                            {Math.round(character.personality.authenticity * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-indigo-500 h-2 rounded-full"
                            style={{
                              width: `${character.personality.authenticity * 100}%`,
                            }}
                          ></div>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {character.personality.communication_style && (
                      <div>
                        <span className="text-slate-400">Communication Style:</span>{" "}
                        <span className="text-slate-200">
                          {character.personality.communication_style}
                        </span>
                      </div>
                    )}
                    {character.personality.content_tone && (
                      <div>
                        <span className="text-slate-400">Content Tone:</span>{" "}
                        <span className="text-slate-200">
                          {character.personality.content_tone}
                        </span>
                      </div>
                    )}
                    {character.personality.temperature !== null && (
                      <div>
                        <span className="text-slate-400">Temperature:</span>{" "}
                        <span className="text-slate-200">
                          {character.personality.temperature}
                        </span>
                      </div>
                    )}
                  </div>
                  {character.personality.preferred_topics &&
                    character.personality.preferred_topics.length > 0 && (
                      <div className="mt-4">
                        <span className="text-slate-400">Preferred Topics: </span>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {character.personality.preferred_topics.map((topic, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-slate-700 text-slate-300 rounded text-sm"
                            >
                              {topic}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                </div>
              )}

              {/* Appearance Section */}
              {character.appearance && (
                <div className="mb-6">
                  <h3 className="text-xl font-semibold mb-4">Appearance</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {character.appearance.hair_color && (
                      <div>
                        <span className="text-slate-400">Hair Color:</span>{" "}
                        <span className="text-slate-200">
                          {character.appearance.hair_color}
                        </span>
                      </div>
                    )}
                    {character.appearance.eye_color && (
                      <div>
                        <span className="text-slate-400">Eye Color:</span>{" "}
                        <span className="text-slate-200">
                          {character.appearance.eye_color}
                        </span>
                      </div>
                    )}
                    {character.appearance.base_model && (
                      <div>
                        <span className="text-slate-400">Base Model:</span>{" "}
                        <span className="text-slate-200">
                          {character.appearance.base_model}
                        </span>
                      </div>
                    )}
                    {character.appearance.face_consistency_method && (
                      <div>
                        <span className="text-slate-400">Face Consistency:</span>{" "}
                        <span className="text-slate-200">
                          {character.appearance.face_consistency_method}
                        </span>
                      </div>
                    )}
                  </div>
                  {character.appearance.face_reference_image_url && (
                    <div className="mt-4">
                      <span className="text-slate-400 block mb-2">Face Reference:</span>
                      <img
                        src={character.appearance.face_reference_image_url}
                        alt="Face reference"
                        className="w-32 h-32 rounded-lg object-cover"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Stats Placeholder */}
              <div className="mt-6">
                <h3 className="text-xl font-semibold mb-4">Stats</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="bg-slate-700 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-indigo-400">0</div>
                    <div className="text-sm text-slate-400 mt-1">Posts</div>
                  </div>
                  <div className="bg-slate-700 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-indigo-400">0</div>
                    <div className="text-sm text-slate-400 mt-1">Followers</div>
                  </div>
                  <div className="bg-slate-700 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-indigo-400">0</div>
                    <div className="text-sm text-slate-400 mt-1">Engagement</div>
                  </div>
                  <div className="bg-slate-700 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-indigo-400">0</div>
                    <div className="text-sm text-slate-400 mt-1">Platforms</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "content" && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold">Content Library</h2>
                <div className="text-sm text-slate-400">
                  {contentTotal} {contentTotal === 1 ? "item" : "items"}
                </div>
              </div>

              {contentLoading && (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
                  <p className="mt-4 text-slate-400">Loading content...</p>
                </div>
              )}

              {contentError && (
                <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4 mb-6">
                  <p className="text-red-400">Error: {contentError}</p>
                </div>
              )}

              {!contentLoading && !contentError && contentItems.length === 0 && (
                <div className="text-center py-12 text-slate-400">
                  <p>No content generated yet.</p>
                  <p className="text-sm mt-2">
                    Generate content for this character to see it here.
                  </p>
                  <Link
                    href="/generate"
                    className="mt-4 inline-block px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
                  >
                    Go to Generate
                  </Link>
                </div>
              )}

              {!contentLoading && !contentError && contentItems.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {contentItems.map((item) => (
                    <div
                      key={item.id}
                      className="bg-slate-700 border border-slate-600 rounded-lg overflow-hidden hover:border-indigo-500/50 transition-all"
                    >
                      {item.thumbnail_url || item.file_url ? (
                        <div className="aspect-square bg-slate-800">
                          <img
                            src={item.thumbnail_url || item.file_url || ""}
                            alt={item.prompt || "Content"}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      ) : (
                        <div className="aspect-square bg-slate-800 flex items-center justify-center">
                          <span className="text-slate-500 text-sm">
                            {item.content_type === "image" ? "🖼️" : item.content_type === "video" ? "🎥" : "📄"}
                          </span>
                        </div>
                      )}
                      <div className="p-3">
                        {item.prompt && (
                          <p className="text-sm text-slate-300 line-clamp-2 mb-2">
                            {item.prompt}
                          </p>
                        )}
                        <div className="flex items-center justify-between text-xs text-slate-400">
                          <span className="capitalize">{item.content_type}</span>
                          {item.created_at && (
                            <span>{new Date(item.created_at).toLocaleDateString()}</span>
                          )}
                        </div>
                        {item.quality_score !== null && (
                          <div className="mt-2">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-slate-400">Quality</span>
                              <span className="text-slate-300">
                                {Math.round(item.quality_score * 100)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-600 rounded-full h-1.5">
                              <div
                                className="bg-indigo-500 h-1.5 rounded-full"
                                style={{ width: `${item.quality_score * 100}%` }}
                              ></div>
                            </div>
                          </div>
                        )}
                        {item.file_url && (
                          <a
                            href={item.file_url}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-2 inline-block w-full text-center px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded transition-colors"
                          >
                            View
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "activity" && (
            <div>
              <h2 className="text-2xl font-semibold mb-6">Activity Timeline</h2>
              <div className="text-center py-12 text-slate-400">
                <p>No activity recorded yet.</p>
                <p className="text-sm mt-2">
                  Activity will appear here once automation features are implemented.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

