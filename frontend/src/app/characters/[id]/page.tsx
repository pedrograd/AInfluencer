"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet, apiPut, API_BASE_URL, getCharacterStyles, createCharacterStyle, updateCharacterStyle, deleteCharacterStyle, type ImageStyle, type ImageStyleCreate } from "@/lib/api";

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

export default function CharacterDetailPage() {
  const params = useParams();
  const characterId = params.id as string;
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "content" | "styles" | "activity">("overview");
  const [contentItems, setContentItems] = useState<ContentItem[]>([]);
  const [contentLoading, setContentLoading] = useState(false);
  const [contentError, setContentError] = useState<string | null>(null);
  const [contentTotal, setContentTotal] = useState(0);
  const [styles, setStyles] = useState<ImageStyle[]>([]);
  const [stylesLoading, setStylesLoading] = useState(false);
  const [stylesError, setStylesError] = useState<string | null>(null);
  const [showStyleModal, setShowStyleModal] = useState(false);
  const [editingStyle, setEditingStyle] = useState<ImageStyle | null>(null);
  const [styleFormData, setStyleFormData] = useState<ImageStyleCreate>({
    name: "",
    description: "",
    display_order: 0,
    is_active: true,
    is_default: false,
  });
  const [previewContent, setPreviewContent] = useState<ContentItem | null>(null);
  const [editingContent, setEditingContent] = useState<ContentItem | null>(null);

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

  useEffect(() => {
    const fetchStyles = async () => {
      if (activeTab !== "styles" || !characterId) return;
      
      try {
        setStylesLoading(true);
        setStylesError(null);
        const stylesList = await getCharacterStyles(characterId);
        setStyles(stylesList);
      } catch (err) {
        setStylesError(err instanceof Error ? err.message : "Failed to load styles");
      } finally {
        setStylesLoading(false);
      }
    };

    fetchStyles();
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

  const handleCreateStyle = () => {
    setEditingStyle(null);
    setStyleFormData({
      name: "",
      description: "",
      display_order: 0,
      is_active: true,
      is_default: false,
    });
    setShowStyleModal(true);
  };

  const handleEditStyle = (style: ImageStyle) => {
    setEditingStyle(style);
    setStyleFormData({
      name: style.name,
      description: style.description || "",
      prompt_prefix: style.prompt_prefix || "",
      prompt_suffix: style.prompt_suffix || "",
      negative_prompt_addition: style.negative_prompt_addition || "",
      checkpoint: style.checkpoint || "",
      sampler_name: style.sampler_name || "",
      scheduler: style.scheduler || "",
      steps: style.steps || undefined,
      cfg: style.cfg || undefined,
      width: style.width || undefined,
      height: style.height || undefined,
      style_keywords: style.style_keywords || [],
      display_order: style.display_order,
      is_active: style.is_active,
      is_default: style.is_default,
    });
    setShowStyleModal(true);
  };

  const handleSaveStyle = async () => {
    if (!characterId) return;
    try {
      if (editingStyle) {
        await updateCharacterStyle(characterId, editingStyle.id, styleFormData);
      } else {
        await createCharacterStyle(characterId, styleFormData);
      }
      setShowStyleModal(false);
      // Refresh styles list
      const stylesList = await getCharacterStyles(characterId);
      setStyles(stylesList);
    } catch (err) {
      setStylesError(err instanceof Error ? err.message : "Failed to save style");
    }
  };

  const handleDeleteStyle = async (styleId: string) => {
    if (!characterId) return;
    if (!confirm("Are you sure you want to delete this style?")) return;
    try {
      await deleteCharacterStyle(characterId, styleId);
      // Refresh styles list
      const stylesList = await getCharacterStyles(characterId);
      setStyles(stylesList);
    } catch (err) {
      setStylesError(err instanceof Error ? err.message : "Failed to delete style");
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
              onClick={() => setActiveTab("styles")}
              className={`pb-3 px-1 font-medium transition-colors ${
                activeTab === "styles"
                  ? "text-indigo-400 border-b-2 border-indigo-400"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              Styles
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
                      className="bg-slate-700 border border-slate-600 rounded-lg overflow-hidden hover:border-indigo-500/50 transition-all cursor-pointer"
                      onClick={() => setPreviewContent(item)}
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
                        <div className="mt-2 flex gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setPreviewContent(item);
                            }}
                            className="flex-1 text-center px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded transition-colors"
                          >
                            Preview
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingContent(item);
                            }}
                            className="flex-1 text-center px-3 py-1.5 bg-slate-600 hover:bg-slate-700 text-white text-xs font-medium rounded transition-colors"
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "styles" && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold">Image Styles</h2>
                <button
                  onClick={handleCreateStyle}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
                >
                  Create Style
                </button>
              </div>

              {stylesLoading && (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
                  <p className="mt-4 text-slate-400">Loading styles...</p>
                </div>
              )}

              {stylesError && (
                <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4 mb-6">
                  <p className="text-red-400">Error: {stylesError}</p>
                </div>
              )}

              {!stylesLoading && !stylesError && styles.length === 0 && (
                <div className="text-center py-12 text-slate-400">
                  <p>No image styles created yet.</p>
                  <p className="text-sm mt-2">
                    Create a style to customize image generation settings for this character.
                  </p>
                </div>
              )}

              {!stylesLoading && !stylesError && styles.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {styles.map((style) => (
                    <div
                      key={style.id}
                      className="bg-slate-700 border border-slate-600 rounded-lg p-4"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-slate-100 mb-1">
                            {style.name}
                          </h3>
                          {style.is_default && (
                            <span className="inline-block px-2 py-0.5 bg-indigo-600 text-white text-xs font-medium rounded">
                              Default
                            </span>
                          )}
                        </div>
                        {!style.is_active && (
                          <span className="px-2 py-0.5 bg-slate-600 text-slate-300 text-xs rounded">
                            Inactive
                          </span>
                        )}
                      </div>
                      {style.description && (
                        <p className="text-sm text-slate-300 mb-3 line-clamp-2">
                          {style.description}
                        </p>
                      )}
                      <div className="space-y-2 text-sm">
                        {style.checkpoint && (
                          <div>
                            <span className="text-slate-400">Checkpoint:</span>{" "}
                            <span className="text-slate-200">{style.checkpoint}</span>
                          </div>
                        )}
                        {style.width && style.height && (
                          <div>
                            <span className="text-slate-400">Size:</span>{" "}
                            <span className="text-slate-200">
                              {style.width}×{style.height}
                            </span>
                          </div>
                        )}
                        {style.steps && (
                          <div>
                            <span className="text-slate-400">Steps:</span>{" "}
                            <span className="text-slate-200">{style.steps}</span>
                          </div>
                        )}
                      </div>
                      {style.style_keywords && style.style_keywords.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-slate-600">
                          <div className="flex flex-wrap gap-1">
                            {style.style_keywords.map((keyword, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 bg-slate-600 text-slate-300 text-xs rounded"
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      <div className="mt-4 flex gap-2">
                        <button
                          onClick={() => handleEditStyle(style)}
                          className="flex-1 px-3 py-2 bg-slate-600 hover:bg-slate-500 text-white text-sm font-medium rounded transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteStyle(style.id)}
                          className="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-sm font-medium rounded transition-colors"
                        >
                          Delete
                        </button>
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

      {/* Style Create/Edit Modal */}
      {showStyleModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold">
                {editingStyle ? "Edit Style" : "Create Style"}
              </h2>
              <button
                onClick={() => setShowStyleModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  value={styleFormData.name}
                  onChange={(e) =>
                    setStyleFormData({ ...styleFormData, name: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="e.g., Casual, Formal, Glamour"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  value={styleFormData.description || ""}
                  onChange={(e) =>
                    setStyleFormData({
                      ...styleFormData,
                      description: e.target.value,
                    })
                  }
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Describe this style..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Display Order
                  </label>
                  <input
                    type="number"
                    value={styleFormData.display_order}
                    onChange={(e) =>
                      setStyleFormData({
                        ...styleFormData,
                        display_order: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Checkpoint
                  </label>
                  <input
                    type="text"
                    value={styleFormData.checkpoint || ""}
                    onChange={(e) =>
                      setStyleFormData({
                        ...styleFormData,
                        checkpoint: e.target.value || undefined,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="e.g., realistic-vision-v6"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Prompt Prefix
                </label>
                <input
                  type="text"
                  value={styleFormData.prompt_prefix || ""}
                  onChange={(e) =>
                    setStyleFormData({
                      ...styleFormData,
                      prompt_prefix: e.target.value || undefined,
                    })
                  }
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Text to prepend to prompt"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Prompt Suffix
                </label>
                <input
                  type="text"
                  value={styleFormData.prompt_suffix || ""}
                  onChange={(e) =>
                    setStyleFormData({
                      ...styleFormData,
                      prompt_suffix: e.target.value || undefined,
                    })
                  }
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Text to append to prompt"
                />
              </div>

              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={styleFormData.is_active}
                    onChange={(e) =>
                      setStyleFormData({
                        ...styleFormData,
                        is_active: e.target.checked,
                      })
                    }
                    className="w-4 h-4 text-indigo-600 bg-slate-700 border-slate-600 rounded focus:ring-indigo-500"
                  />
                  <span className="text-sm text-slate-300">Active</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={styleFormData.is_default}
                    onChange={(e) =>
                      setStyleFormData({
                        ...styleFormData,
                        is_default: e.target.checked,
                      })
                    }
                    className="w-4 h-4 text-indigo-600 bg-slate-700 border-slate-600 rounded focus:ring-indigo-500"
                  />
                  <span className="text-sm text-slate-300">Default</span>
                </label>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleSaveStyle}
                  className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
                >
                  {editingStyle ? "Update" : "Create"}
                </button>
                <button
                  onClick={() => setShowStyleModal(false)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content Preview Modal */}
      {previewContent && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setPreviewContent(null)}>
          <div className="bg-slate-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-white">Content Preview</h2>
                <button
                  onClick={() => setPreviewContent(null)}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  ✕
                </button>
              </div>
              
              <div className="mb-6">
                {previewContent.file_url || previewContent.thumbnail_url ? (
                  <div className="bg-slate-900 rounded-lg overflow-hidden">
                    <img
                      src={previewContent.file_url || previewContent.thumbnail_url || ""}
                      alt={previewContent.prompt || "Content"}
                      className="w-full h-auto max-h-[60vh] object-contain mx-auto"
                    />
                  </div>
                ) : (
                  <div className="bg-slate-900 rounded-lg aspect-video flex items-center justify-center">
                    <span className="text-slate-500 text-4xl">
                      {previewContent.content_type === "image" ? "🖼️" : previewContent.content_type === "video" ? "🎥" : "📄"}
                    </span>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Basic Info</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-slate-400">Type:</span>{" "}
                      <span className="text-white capitalize">{previewContent.content_type}</span>
                    </div>
                    {previewContent.content_category && (
                      <div>
                        <span className="text-slate-400">Category:</span>{" "}
                        <span className="text-white capitalize">{previewContent.content_category}</span>
                      </div>
                    )}
                    {previewContent.created_at && (
                      <div>
                        <span className="text-slate-400">Created:</span>{" "}
                        <span className="text-white">{new Date(previewContent.created_at).toLocaleString()}</span>
                      </div>
                    )}
                    {previewContent.width && previewContent.height && (
                      <div>
                        <span className="text-slate-400">Dimensions:</span>{" "}
                        <span className="text-white">{previewContent.width} × {previewContent.height}</span>
                      </div>
                    )}
                    {previewContent.file_size && (
                      <div>
                        <span className="text-slate-400">Size:</span>{" "}
                        <span className="text-white">{(previewContent.file_size / 1024 / 1024).toFixed(2)} MB</span>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Status</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-slate-400">Approval:</span>{" "}
                      <span className={`capitalize ${previewContent.approval_status === "approved" ? "text-green-400" : previewContent.approval_status === "rejected" ? "text-red-400" : "text-yellow-400"}`}>
                        {previewContent.approval_status || "pending"}
                      </span>
                    </div>
                    {previewContent.quality_score !== null && (
                      <div>
                        <span className="text-slate-400">Quality:</span>{" "}
                        <span className="text-white">{Math.round(previewContent.quality_score * 100)}%</span>
                      </div>
                    )}
                    <div>
                      <span className="text-slate-400">NSFW:</span>{" "}
                      <span className={previewContent.is_nsfw ? "text-red-400" : "text-green-400"}>
                        {previewContent.is_nsfw ? "Yes" : "No"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {previewContent.prompt && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Prompt</h3>
                  <p className="text-sm text-slate-300 bg-slate-900 p-3 rounded-lg">{previewContent.prompt}</p>
                </div>
              )}

              {previewContent.negative_prompt && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Negative Prompt</h3>
                  <p className="text-sm text-slate-300 bg-slate-900 p-3 rounded-lg">{previewContent.negative_prompt}</p>
                </div>
              )}

              {previewContent.description && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Description</h3>
                  <p className="text-sm text-slate-300 bg-slate-900 p-3 rounded-lg">{previewContent.description}</p>
                </div>
              )}

              {previewContent.tags && previewContent.tags.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {previewContent.tags.map((tag, idx) => (
                      <span key={idx} className="px-2 py-1 bg-indigo-600/20 text-indigo-300 text-xs rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    setEditingContent(previewContent);
                    setPreviewContent(null);
                  }}
                  className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={() => setPreviewContent(null)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content Edit Modal */}
      {editingContent && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setEditingContent(null)}>
          <div className="bg-slate-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-white">Edit Content</h2>
                <button
                  onClick={() => setEditingContent(null)}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  ✕
                </button>
              </div>

              <ContentEditForm
                content={editingContent}
                onSave={async (updates) => {
                  try {
                    const response = await apiPut<{ ok: boolean; content: any }>(`/api/content/library/${editingContent.id}`, updates);
                    if (response.ok) {
                      // Update the content item in the list
                      setContentItems(items => items.map(item => 
                        item.id === editingContent.id ? { ...item, ...response.content } : item
                      ));
                      setEditingContent(null);
                    }
                  } catch (err) {
                    alert(err instanceof Error ? err.message : "Failed to update content");
                  }
                }}
                onCancel={() => setEditingContent(null)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Content Edit Form Component
function ContentEditForm({ content, onSave, onCancel }: { content: ContentItem; onSave: (updates: any) => Promise<void>; onCancel: () => void }) {
  const [description, setDescription] = useState(content.description || "");
  const [tags, setTags] = useState<string[]>(content.tags || []);
  const [tagInput, setTagInput] = useState("");
  const [approvalStatus, setApprovalStatus] = useState(content.approval_status || "pending");
  const [qualityScore, setQualityScore] = useState(content.quality_score?.toString() || "");
  const [folderPath, setFolderPath] = useState(content.folder_path || "");
  const [saving, setSaving] = useState(false);

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(t => t !== tagToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updates: any = {};
      if (description !== (content.description || "")) updates.description = description;
      if (JSON.stringify(tags.sort()) !== JSON.stringify((content.tags || []).sort())) updates.tags = tags;
      if (approvalStatus !== content.approval_status) updates.approval_status = approvalStatus;
      if (qualityScore && parseFloat(qualityScore) !== content.quality_score) {
        const score = parseFloat(qualityScore);
        if (score >= 0 && score <= 1) updates.quality_score = score;
      }
      if (folderPath !== (content.folder_path || "")) updates.folder_path = folderPath;
      
      await onSave(updates);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Enter content description..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">Tags</label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), handleAddTag())}
            className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Add tag..."
          />
          <button
            type="button"
            onClick={handleAddTag}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
          >
            Add
          </button>
        </div>
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {tags.map((tag, idx) => (
              <span key={idx} className="px-2 py-1 bg-indigo-600/20 text-indigo-300 text-xs rounded flex items-center gap-1">
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="hover:text-red-400"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">Approval Status</label>
        <select
          value={approvalStatus}
          onChange={(e) => setApprovalStatus(e.target.value)}
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">Quality Score (0.0 - 1.0)</label>
        <input
          type="number"
          min="0"
          max="1"
          step="0.01"
          value={qualityScore}
          onChange={(e) => setQualityScore(e.target.value)}
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="0.0 - 1.0"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">Folder Path</label>
        <input
          type="text"
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="e.g., /folder/subfolder"
        />
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={saving}
          className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
        >
          {saving ? "Saving..." : "Save Changes"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

