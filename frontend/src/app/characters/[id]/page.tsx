"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  apiGet,
  apiPut,
  API_BASE_URL,
  getCharacterStyles,
  createCharacterStyle,
  updateCharacterStyle,
  deleteCharacterStyle,
  type ImageStyle,
  type ImageStyleCreate,
} from "@/lib/api";
import {
  PageHeader,
  SectionCard,
  PrimaryButton,
  SecondaryButton,
  IconButton,
  StatusChip,
  LoadingSkeleton,
  EmptyState,
  Alert,
  ErrorBanner,
  Input,
  Textarea,
  Select,
  FormGroup,
} from "@/components/ui";
import {
  ArrowLeft,
  Edit,
  Settings,
  Image as ImageIcon,
  Palette,
  Activity,
  Plus,
  Trash2,
  X,
  Eye,
} from "lucide-react";

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
  const router = useRouter();
  const characterId = params.id as string;
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "content" | "styles" | "activity"
  >("overview");
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
  const [previewContent, setPreviewContent] = useState<ContentItem | null>(
    null
  );
  const [editingContent, setEditingContent] = useState<ContentItem | null>(
    null
  );

  useEffect(() => {
    const fetchCharacter = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiGet<CharacterResponse>(
          `/api/characters/${characterId}`
        );
        if (response.success) {
          setCharacter(response.data);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load character"
        );
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
        const response = await apiGet<ContentLibraryResponse>(
          `/api/content/library?${params.toString()}`
        );
        if (response.ok) {
          setContentItems(response.items || []);
          setContentTotal(response.total || 0);
        } else {
          setContentError(response.error || "Failed to load content");
        }
      } catch (err) {
        setContentError(
          err instanceof Error ? err.message : "Failed to load content"
        );
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
        setStylesError(
          err instanceof Error ? err.message : "Failed to load styles"
        );
      } finally {
        setStylesLoading(false);
      }
    };

    fetchStyles();
  }, [activeTab, characterId]);

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
      const stylesList = await getCharacterStyles(characterId);
      setStyles(stylesList);
    } catch (err) {
      setStylesError(
        err instanceof Error ? err.message : "Failed to save style"
      );
    }
  };

  const handleDeleteStyle = async (styleId: string) => {
    if (!characterId) return;
    if (!confirm("Are you sure you want to delete this style?")) return;
    try {
      await deleteCharacterStyle(characterId, styleId);
      const stylesList = await getCharacterStyles(characterId);
      setStyles(stylesList);
    } catch (err) {
      setStylesError(
        err instanceof Error ? err.message : "Failed to delete style"
      );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)]">
        <main className="container mx-auto px-6 py-8">
          <div className="text-center py-12">
            <LoadingSkeleton variant="card" height="200px" />
            <p className="mt-4 text-[var(--text-secondary)]">
              Loading character...
            </p>
          </div>
        </main>
      </div>
    );
  }

  if (error || !character) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)]">
        <main className="container mx-auto px-6 py-8">
          <Link
            href="/characters"
            className="text-[var(--accent-primary)] hover:text-[var(--accent-primary-hover)] mb-4 inline-flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Characters
          </Link>
          <ErrorBanner
            title="Error loading character"
            message={error || "Character not found"}
            remediation={{
              label: "Go Back",
              onClick: () => router.push("/characters"),
            }}
          />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        <PageHeader
          title={character.name}
          description={`Created: ${new Date(
            character.created_at
          ).toLocaleDateString()}`}
          action={
            <div className="flex gap-2">
              <SecondaryButton
                icon={<Edit className="h-4 w-4" />}
                onClick={() => router.push(`/characters/${characterId}/edit`)}
              >
                Edit
              </SecondaryButton>
              <SecondaryButton
                icon={<Settings className="h-4 w-4" />}
                variant="ghost"
              >
                Settings
              </SecondaryButton>
            </div>
          }
          tabs={[
            { id: "overview", label: "Overview" },
            { id: "content", label: "Content" },
            { id: "styles", label: "Styles" },
            { id: "activity", label: "Activity" },
          ]}
          activeTab={activeTab}
          onTabChange={(tabId) => setActiveTab(tabId as typeof activeTab)}
        />

        {/* Character Header Card */}
        <SectionCard className="mb-8">
          <div className="flex flex-col sm:flex-row gap-6">
            <div className="flex-shrink-0">
              {character.profile_image_url ? (
                <img
                  src={character.profile_image_url}
                  alt={character.name}
                  className="w-32 h-32 rounded-lg object-cover"
                />
              ) : (
                <div className="w-32 h-32 bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] rounded-lg flex items-center justify-center">
                  <span className="text-4xl text-white font-bold">
                    {character.name.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
            </div>

            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <StatusChip
                  status={getStatusChipStatus(character.status)}
                  label={character.status}
                />
                <span className="text-sm text-[var(--text-secondary)]">
                  {character.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              {character.bio && (
                <p className="text-[var(--text-primary)] mb-4">
                  {character.bio}
                </p>
              )}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                {character.age && (
                  <div>
                    <span className="text-[var(--text-secondary)]">Age:</span>{" "}
                    <span className="text-[var(--text-primary)]">
                      {character.age}
                    </span>
                  </div>
                )}
                {character.location && (
                  <div>
                    <span className="text-[var(--text-secondary)]">
                      Location:
                    </span>{" "}
                    <span className="text-[var(--text-primary)]">
                      {character.location}
                    </span>
                  </div>
                )}
                <div>
                  <span className="text-[var(--text-secondary)]">
                    Timezone:
                  </span>{" "}
                  <span className="text-[var(--text-primary)]">
                    {character.timezone}
                  </span>
                </div>
                <div>
                  <span className="text-[var(--text-secondary)]">Status:</span>{" "}
                  <StatusChip
                    status={character.is_active ? "success" : "warning"}
                    label={character.is_active ? "Active" : "Inactive"}
                  />
                </div>
              </div>
              {character.interests && character.interests.length > 0 && (
                <div className="mt-4">
                  <span className="text-[var(--text-secondary)] text-sm">
                    Interests:{" "}
                  </span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {character.interests.map((interest, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-[var(--bg-surface)] text-[var(--text-primary)] rounded text-sm border border-[var(--border-base)]"
                      >
                        {interest}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </SectionCard>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div className="space-y-8">
            {/* Personality Section */}
            {character.personality && (
              <SectionCard title="Personality Traits">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {character.personality.extroversion !== null && (
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-[var(--text-secondary)]">
                          Extroversion
                        </span>
                        <span className="text-[var(--text-primary)]">
                          {Math.round(character.personality.extroversion * 100)}
                          %
                        </span>
                      </div>
                      <div className="w-full bg-[var(--bg-surface)] rounded-full h-2">
                        <div
                          className="bg-[var(--accent-primary)] h-2 rounded-full transition-all"
                          style={{
                            width: `${
                              character.personality.extroversion * 100
                            }%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                  {character.personality.creativity !== null && (
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-[var(--text-secondary)]">
                          Creativity
                        </span>
                        <span className="text-[var(--text-primary)]">
                          {Math.round(character.personality.creativity * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-[var(--bg-surface)] rounded-full h-2">
                        <div
                          className="bg-[var(--accent-primary)] h-2 rounded-full transition-all"
                          style={{
                            width: `${character.personality.creativity * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                  {character.personality.humor !== null && (
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-[var(--text-secondary)]">
                          Humor
                        </span>
                        <span className="text-[var(--text-primary)]">
                          {Math.round(character.personality.humor * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-[var(--bg-surface)] rounded-full h-2">
                        <div
                          className="bg-[var(--accent-primary)] h-2 rounded-full transition-all"
                          style={{
                            width: `${character.personality.humor * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                  {character.personality.professionalism !== null && (
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-[var(--text-secondary)]">
                          Professionalism
                        </span>
                        <span className="text-[var(--text-primary)]">
                          {Math.round(
                            character.personality.professionalism * 100
                          )}
                          %
                        </span>
                      </div>
                      <div className="w-full bg-[var(--bg-surface)] rounded-full h-2">
                        <div
                          className="bg-[var(--accent-primary)] h-2 rounded-full transition-all"
                          style={{
                            width: `${
                              character.personality.professionalism * 100
                            }%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                  {character.personality.authenticity !== null && (
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-[var(--text-secondary)]">
                          Authenticity
                        </span>
                        <span className="text-[var(--text-primary)]">
                          {Math.round(character.personality.authenticity * 100)}
                          %
                        </span>
                      </div>
                      <div className="w-full bg-[var(--bg-surface)] rounded-full h-2">
                        <div
                          className="bg-[var(--accent-primary)] h-2 rounded-full transition-all"
                          style={{
                            width: `${
                              character.personality.authenticity * 100
                            }%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
                <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {character.personality.communication_style && (
                    <div>
                      <span className="text-[var(--text-secondary)]">
                        Communication Style:
                      </span>{" "}
                      <span className="text-[var(--text-primary)]">
                        {character.personality.communication_style}
                      </span>
                    </div>
                  )}
                  {character.personality.content_tone && (
                    <div>
                      <span className="text-[var(--text-secondary)]">
                        Content Tone:
                      </span>{" "}
                      <span className="text-[var(--text-primary)]">
                        {character.personality.content_tone}
                      </span>
                    </div>
                  )}
                  {character.personality.temperature !== null && (
                    <div>
                      <span className="text-[var(--text-secondary)]">
                        Temperature:
                      </span>{" "}
                      <span className="text-[var(--text-primary)]">
                        {character.personality.temperature}
                      </span>
                    </div>
                  )}
                </div>
                {character.personality.preferred_topics &&
                  character.personality.preferred_topics.length > 0 && (
                    <div className="mt-4">
                      <span className="text-[var(--text-secondary)]">
                        Preferred Topics:{" "}
                      </span>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {character.personality.preferred_topics.map(
                          (topic, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-[var(--bg-surface)] text-[var(--text-primary)] rounded text-sm border border-[var(--border-base)]"
                            >
                              {topic}
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  )}
              </SectionCard>
            )}

            {/* Appearance Section */}
            {character.appearance && (
              <SectionCard title="Appearance">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {character.appearance.hair_color && (
                    <div>
                      <span className="text-[var(--text-secondary)]">
                        Hair Color:
                      </span>{" "}
                      <span className="text-[var(--text-primary)]">
                        {character.appearance.hair_color}
                      </span>
                    </div>
                  )}
                  {character.appearance.eye_color && (
                    <div>
                      <span className="text-[var(--text-secondary)]">
                        Eye Color:
                      </span>{" "}
                      <span className="text-[var(--text-primary)]">
                        {character.appearance.eye_color}
                      </span>
                    </div>
                  )}
                  {character.appearance.base_model && (
                    <div>
                      <span className="text-[var(--text-secondary)]">
                        Base Model:
                      </span>{" "}
                      <span className="text-[var(--text-primary)]">
                        {character.appearance.base_model}
                      </span>
                    </div>
                  )}
                  {character.appearance.face_consistency_method && (
                    <div>
                      <span className="text-[var(--text-secondary)]">
                        Face Consistency:
                      </span>{" "}
                      <span className="text-[var(--text-primary)]">
                        {character.appearance.face_consistency_method}
                      </span>
                    </div>
                  )}
                </div>
                {character.appearance.face_reference_image_url && (
                  <div className="mt-4">
                    <span className="text-[var(--text-secondary)] block mb-2">
                      Face Reference:
                    </span>
                    <img
                      src={character.appearance.face_reference_image_url}
                      alt="Face reference"
                      className="w-32 h-32 rounded-lg object-cover border border-[var(--border-base)]"
                    />
                  </div>
                )}
              </SectionCard>
            )}

            {/* Stats Placeholder */}
            <SectionCard title="Stats">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-[var(--bg-surface)] rounded-lg p-4 text-center border border-[var(--border-base)]">
                  <div className="text-2xl font-bold text-[var(--accent-primary)]">
                    0
                  </div>
                  <div className="text-sm text-[var(--text-secondary)] mt-1">
                    Posts
                  </div>
                </div>
                <div className="bg-[var(--bg-surface)] rounded-lg p-4 text-center border border-[var(--border-base)]">
                  <div className="text-2xl font-bold text-[var(--accent-primary)]">
                    0
                  </div>
                  <div className="text-sm text-[var(--text-secondary)] mt-1">
                    Followers
                  </div>
                </div>
                <div className="bg-[var(--bg-surface)] rounded-lg p-4 text-center border border-[var(--border-base)]">
                  <div className="text-2xl font-bold text-[var(--accent-primary)]">
                    0
                  </div>
                  <div className="text-sm text-[var(--text-secondary)] mt-1">
                    Engagement
                  </div>
                </div>
                <div className="bg-[var(--bg-surface)] rounded-lg p-4 text-center border border-[var(--border-base)]">
                  <div className="text-2xl font-bold text-[var(--accent-primary)]">
                    0
                  </div>
                  <div className="text-sm text-[var(--text-secondary)] mt-1">
                    Platforms
                  </div>
                </div>
              </div>
            </SectionCard>
          </div>
        )}

        {activeTab === "content" && (
          <SectionCard
            title="Content Library"
            description={`${contentTotal} ${
              contentTotal === 1 ? "item" : "items"
            }`}
            loading={contentLoading}
            empty={!contentLoading && contentItems.length === 0}
            emptyMessage="No content generated yet"
          >
            {contentError && (
              <Alert message={contentError} variant="error" className="mb-4" />
            )}
            {!contentLoading && !contentError && contentItems.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {contentItems.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] overflow-hidden hover:border-[var(--accent-primary)] transition-all cursor-pointer"
                    onClick={() => setPreviewContent(item)}
                  >
                    {item.thumbnail_url || item.file_url ? (
                      <div className="aspect-square bg-[var(--bg-surface)]">
                        <img
                          src={item.thumbnail_url || item.file_url || ""}
                          alt={item.prompt || "Content"}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    ) : (
                      <div className="aspect-square bg-[var(--bg-surface)] flex items-center justify-center">
                        <ImageIcon className="h-12 w-12 text-[var(--text-muted)]" />
                      </div>
                    )}
                    <div className="p-3">
                      {item.prompt && (
                        <p className="text-sm text-[var(--text-primary)] line-clamp-2 mb-2">
                          {item.prompt}
                        </p>
                      )}
                      <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
                        <span className="capitalize">{item.content_type}</span>
                        {item.created_at && (
                          <span>
                            {new Date(item.created_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      {item.quality_score !== null && (
                        <div className="mt-2">
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-[var(--text-secondary)]">
                              Quality
                            </span>
                            <span className="text-[var(--text-primary)]">
                              {Math.round(item.quality_score * 100)}%
                            </span>
                          </div>
                          <div className="w-full bg-[var(--bg-surface)] rounded-full h-1.5">
                            <div
                              className="bg-[var(--accent-primary)] h-1.5 rounded-full transition-all"
                              style={{ width: `${item.quality_score * 100}%` }}
                            />
                          </div>
                        </div>
                      )}
                      <div className="mt-2 flex gap-2">
                        <SecondaryButton
                          size="sm"
                          icon={<Eye className="h-3 w-3" />}
                          onClick={(e) => {
                            e.stopPropagation();
                            setPreviewContent(item);
                          }}
                          className="flex-1"
                        >
                          Preview
                        </SecondaryButton>
                        <SecondaryButton
                          size="sm"
                          icon={<Edit className="h-3 w-3" />}
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingContent(item);
                          }}
                          className="flex-1"
                        >
                          Edit
                        </SecondaryButton>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {!contentLoading && !contentError && contentItems.length === 0 && (
              <EmptyState
                icon={<ImageIcon className="h-12 w-12" />}
                title="No content generated yet"
                description="Generate content for this character to see it here."
                action={{
                  label: "Go to Generate",
                  onClick: () => router.push("/generate"),
                }}
              />
            )}
          </SectionCard>
        )}

        {activeTab === "styles" && (
          <SectionCard
            title="Image Styles"
            action={
              <PrimaryButton
                size="sm"
                icon={<Plus className="h-4 w-4" />}
                onClick={handleCreateStyle}
              >
                Create Style
              </PrimaryButton>
            }
            loading={stylesLoading}
            empty={!stylesLoading && styles.length === 0}
            emptyMessage="No image styles created yet"
          >
            {stylesError && (
              <Alert message={stylesError} variant="error" className="mb-4" />
            )}
            {!stylesLoading && !stylesError && styles.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {styles.map((style) => (
                  <div
                    key={style.id}
                    className="rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] p-4"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
                          {style.name}
                        </h3>
                        {style.is_default && (
                          <StatusChip status="info" label="Default" />
                        )}
                      </div>
                      {!style.is_active && (
                        <StatusChip status="warning" label="Inactive" />
                      )}
                    </div>
                    {style.description && (
                      <p className="text-sm text-[var(--text-secondary)] mb-3 line-clamp-2">
                        {style.description}
                      </p>
                    )}
                    <div className="space-y-2 text-sm">
                      {style.checkpoint && (
                        <div>
                          <span className="text-[var(--text-secondary)]">
                            Checkpoint:
                          </span>{" "}
                          <span className="text-[var(--text-primary)]">
                            {style.checkpoint}
                          </span>
                        </div>
                      )}
                      {style.width && style.height && (
                        <div>
                          <span className="text-[var(--text-secondary)]">
                            Size:
                          </span>{" "}
                          <span className="text-[var(--text-primary)]">
                            {style.width}×{style.height}
                          </span>
                        </div>
                      )}
                      {style.steps && (
                        <div>
                          <span className="text-[var(--text-secondary)]">
                            Steps:
                          </span>{" "}
                          <span className="text-[var(--text-primary)]">
                            {style.steps}
                          </span>
                        </div>
                      )}
                    </div>
                    {style.style_keywords &&
                      style.style_keywords.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-[var(--border-base)]">
                          <div className="flex flex-wrap gap-1">
                            {style.style_keywords.map((keyword, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 bg-[var(--bg-surface)] text-[var(--text-primary)] text-xs rounded border border-[var(--border-base)]"
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    <div className="mt-4 flex gap-2">
                      <SecondaryButton
                        size="sm"
                        icon={<Edit className="h-3 w-3" />}
                        onClick={() => handleEditStyle(style)}
                        className="flex-1"
                      >
                        Edit
                      </SecondaryButton>
                      <IconButton
                        icon={<Trash2 className="h-4 w-4" />}
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteStyle(style.id)}
                        aria-label="Delete style"
                        className="text-[var(--error)] hover:bg-[var(--error-bg)]"
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
            {!stylesLoading && !stylesError && styles.length === 0 && (
              <EmptyState
                icon={<Palette className="h-12 w-12" />}
                title="No image styles created yet"
                description="Create a style to customize image generation settings for this character."
                action={{
                  label: "Create Style",
                  onClick: handleCreateStyle,
                }}
              />
            )}
          </SectionCard>
        )}

        {activeTab === "activity" && (
          <SectionCard title="Activity Timeline">
            <EmptyState
              icon={<Activity className="h-12 w-12" />}
              title="No activity recorded yet"
              description="Activity will appear here once automation features are implemented."
              action={{
                label: "Refresh",
                onClick: () => window.location.reload(),
              }}
            />
          </SectionCard>
        )}
      </main>

      {/* Style Create/Edit Modal */}
      {showStyleModal && (
        <div className="fixed inset-0 bg-[var(--bg-overlay)] flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-elevated)] border border-[var(--border-base)] rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-[var(--text-primary)]">
                {editingStyle ? "Edit Style" : "Create Style"}
              </h2>
              <IconButton
                icon={<X className="h-4 w-4" />}
                size="sm"
                variant="ghost"
                onClick={() => setShowStyleModal(false)}
                aria-label="Close modal"
              />
            </div>

            <FormGroup>
              <Input
                label="Name"
                required
                value={styleFormData.name}
                onChange={(e) =>
                  setStyleFormData({ ...styleFormData, name: e.target.value })
                }
                placeholder="e.g., Casual, Formal, Glamour"
              />
              <Textarea
                label="Description"
                value={styleFormData.description || ""}
                onChange={(e) =>
                  setStyleFormData({
                    ...styleFormData,
                    description: e.target.value,
                  })
                }
                placeholder="Describe this style..."
                rows={3}
              />
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Display Order"
                  type="number"
                  value={styleFormData.display_order}
                  onChange={(e) =>
                    setStyleFormData({
                      ...styleFormData,
                      display_order: parseInt(e.target.value) || 0,
                    })
                  }
                />
                <Input
                  label="Checkpoint"
                  value={styleFormData.checkpoint || ""}
                  onChange={(e) =>
                    setStyleFormData({
                      ...styleFormData,
                      checkpoint: e.target.value || undefined,
                    })
                  }
                  placeholder="e.g., realistic-vision-v6"
                />
              </div>
              <Input
                label="Prompt Prefix"
                value={styleFormData.prompt_prefix || ""}
                onChange={(e) =>
                  setStyleFormData({
                    ...styleFormData,
                    prompt_prefix: e.target.value || undefined,
                  })
                }
                placeholder="Text to prepend to prompt"
              />
              <Input
                label="Prompt Suffix"
                value={styleFormData.prompt_suffix || ""}
                onChange={(e) =>
                  setStyleFormData({
                    ...styleFormData,
                    prompt_suffix: e.target.value || undefined,
                  })
                }
                placeholder="Text to append to prompt"
              />
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={styleFormData.is_active}
                    onChange={(e) =>
                      setStyleFormData({
                        ...styleFormData,
                        is_active: e.target.checked,
                      })
                    }
                    className="w-4 h-4 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
                  />
                  <span className="text-sm text-[var(--text-primary)]">
                    Active
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={styleFormData.is_default}
                    onChange={(e) =>
                      setStyleFormData({
                        ...styleFormData,
                        is_default: e.target.checked,
                      })
                    }
                    className="w-4 h-4 text-[var(--accent-primary)] bg-[var(--bg-elevated)] border-[var(--border-base)] rounded focus:ring-[var(--accent-primary)]"
                  />
                  <span className="text-sm text-[var(--text-primary)]">
                    Default
                  </span>
                </label>
              </div>
              <div className="flex gap-3 pt-4">
                <PrimaryButton onClick={handleSaveStyle} className="flex-1">
                  {editingStyle ? "Update" : "Create"}
                </PrimaryButton>
                <SecondaryButton onClick={() => setShowStyleModal(false)}>
                  Cancel
                </SecondaryButton>
              </div>
            </FormGroup>
          </div>
        </div>
      )}

      {/* Content Preview Modal - Simplified for now */}
      {previewContent && (
        <div
          className="fixed inset-0 bg-[var(--bg-overlay)] flex items-center justify-center z-50 p-4"
          onClick={() => setPreviewContent(null)}
        >
          <div
            className="bg-[var(--bg-elevated)] rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-[var(--text-primary)]">
                  Content Preview
                </h2>
                <IconButton
                  icon={<X className="h-4 w-4" />}
                  size="sm"
                  variant="ghost"
                  onClick={() => setPreviewContent(null)}
                  aria-label="Close preview"
                />
              </div>

              <div className="mb-6">
                {previewContent.file_url || previewContent.thumbnail_url ? (
                  <div className="bg-[var(--bg-surface)] rounded-lg overflow-hidden border border-[var(--border-base)]">
                    <img
                      src={
                        previewContent.file_url ||
                        previewContent.thumbnail_url ||
                        ""
                      }
                      alt={previewContent.prompt || "Content"}
                      className="w-full h-auto max-h-[60vh] object-contain mx-auto"
                    />
                  </div>
                ) : (
                  <div className="bg-[var(--bg-surface)] rounded-lg aspect-video flex items-center justify-center border border-[var(--border-base)]">
                    <ImageIcon className="h-16 w-16 text-[var(--text-muted)]" />
                  </div>
                )}
              </div>

              {previewContent.prompt && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-2">
                    Prompt
                  </h3>
                  <p className="text-sm text-[var(--text-primary)] bg-[var(--bg-surface)] p-3 rounded-lg border border-[var(--border-base)]">
                    {previewContent.prompt}
                  </p>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <PrimaryButton
                  onClick={() => {
                    setEditingContent(previewContent);
                    setPreviewContent(null);
                  }}
                  className="flex-1"
                >
                  Edit
                </PrimaryButton>
                <SecondaryButton onClick={() => setPreviewContent(null)}>
                  Close
                </SecondaryButton>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
