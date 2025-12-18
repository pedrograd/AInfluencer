"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet, apiPut } from "@/lib/api";
import {
  PageHeader,
  SectionCard,
  PrimaryButton,
  SecondaryButton,
  Input,
  Textarea,
  Select,
  FormGroup,
  LoadingSkeleton,
  ErrorBanner,
} from "@/components/ui";
import { ArrowLeft, Plus, X } from "lucide-react";

type Character = {
  id: string;
  name: string;
  bio: string | null;
  age: number | null;
  location: string | null;
  timezone: string;
  interests: string[] | null;
  profile_image_url: string | null;
  personality?: {
    extroversion: number | null;
    creativity: number | null;
    humor: number | null;
    professionalism: number | null;
    authenticity: number | null;
    communication_style: string | null;
    preferred_topics: string[] | null;
    content_tone: string | null;
    temperature: number | null;
  };
  appearance?: {
    face_reference_image_url: string | null;
    hair_color: string | null;
    eye_color: string | null;
    base_model: string;
  };
};

type CharacterResponse = {
  success: boolean;
  data: Character;
};

type CharacterFormData = {
  name: string;
  bio: string;
  age: number | null;
  location: string;
  timezone: string;
  interests: string[];
  profile_image_url: string;
  personality: {
    extroversion: number;
    creativity: number;
    humor: number;
    professionalism: number;
    authenticity: number;
    communication_style: string;
    preferred_topics: string[];
    content_tone: string;
    temperature: number;
  } | null;
  appearance: {
    face_reference_image_url: string;
    hair_color: string;
    eye_color: string;
    base_model: string;
  } | null;
};

export default function EditCharacterPage() {
  const params = useParams();
  const router = useRouter();
  const characterId = params.id as string;
  const [activeTab, setActiveTab] = useState<
    "basic" | "personality" | "appearance"
  >("basic");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<CharacterFormData>({
    name: "",
    bio: "",
    age: null,
    location: "",
    timezone: "UTC",
    interests: [],
    profile_image_url: "",
    personality: null,
    appearance: null,
  });
  const [interestInput, setInterestInput] = useState("");

  useEffect(() => {
    const fetchCharacter = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiGet<CharacterResponse>(
          `/api/characters/${characterId}`
        );
        if (response.success) {
          const char = response.data;
          setFormData({
            name: char.name,
            bio: char.bio || "",
            age: char.age,
            location: char.location || "",
            timezone: char.timezone,
            interests: char.interests || [],
            profile_image_url: char.profile_image_url || "",
            personality: char.personality
              ? {
                  extroversion: char.personality.extroversion ?? 0.5,
                  creativity: char.personality.creativity ?? 0.5,
                  humor: char.personality.humor ?? 0.5,
                  professionalism: char.personality.professionalism ?? 0.5,
                  authenticity: char.personality.authenticity ?? 0.5,
                  communication_style:
                    char.personality.communication_style || "",
                  preferred_topics: char.personality.preferred_topics || [],
                  content_tone: char.personality.content_tone || "",
                  temperature: char.personality.temperature ?? 0.7,
                }
              : null,
            appearance: char.appearance
              ? {
                  face_reference_image_url:
                    char.appearance.face_reference_image_url || "",
                  hair_color: char.appearance.hair_color || "",
                  eye_color: char.appearance.eye_color || "",
                  base_model:
                    char.appearance.base_model || "realistic-vision-v6",
                }
              : null,
          });
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const response = await apiPut<{ success: boolean; data: { id: string } }>(
        `/api/characters/${characterId}`,
        {
          name: formData.name,
          bio: formData.bio || null,
          age: formData.age || null,
          location: formData.location || null,
          timezone: formData.timezone,
          interests: formData.interests.length > 0 ? formData.interests : null,
          profile_image_url: formData.profile_image_url || null,
          personality: formData.personality,
          appearance: formData.appearance,
        }
      );

      if (response.success) {
        router.push(`/characters/${characterId}`);
      } else {
        setError("Failed to update character");
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update character"
      );
    } finally {
      setSaving(false);
    }
  };

  const addInterest = () => {
    if (
      interestInput.trim() &&
      !formData.interests.includes(interestInput.trim())
    ) {
      setFormData({
        ...formData,
        interests: [...formData.interests, interestInput.trim()],
      });
      setInterestInput("");
    }
  };

  const removeInterest = (interest: string) => {
    setFormData({
      ...formData,
      interests: formData.interests.filter((i) => i !== interest),
    });
  };

  const updatePersonality = (
    updates: Partial<CharacterFormData["personality"]>
  ) => {
    if (!formData.personality) return;
    setFormData({
      ...formData,
      personality: { ...formData.personality, ...updates },
    });
  };

  const updateAppearance = (
    updates: Partial<CharacterFormData["appearance"]>
  ) => {
    if (!formData.appearance) return;
    setFormData({
      ...formData,
      appearance: { ...formData.appearance, ...updates },
    });
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

  if (error && !formData.name) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)]">
        <main className="container mx-auto px-6 py-8">
          <Link
            href={`/characters/${characterId}`}
            className="text-[var(--accent-primary)] hover:text-[var(--accent-primary-hover)] mb-4 inline-flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Character
          </Link>
          <ErrorBanner
            title="Error loading character"
            message={error}
            remediation={{
              label: "Go Back",
              onClick: () => router.push(`/characters/${characterId}`),
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
          title="Edit Character"
          description="Update character information, personality, and appearance."
          tabs={[
            { id: "basic", label: "Basic Info" },
            { id: "personality", label: "Personality" },
            { id: "appearance", label: "Appearance" },
          ]}
          activeTab={activeTab}
          onTabChange={(tabId) => setActiveTab(tabId as typeof activeTab)}
        />

        {error && (
          <div className="mb-6">
            <ErrorBanner
              title="Error updating character"
              message={error}
              remediation={{
                label: "Try Again",
                onClick: () => setError(null),
              }}
            />
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info Tab */}
          {activeTab === "basic" && (
            <SectionCard title="Basic Information">
              <FormGroup>
                <Input
                  label="Name"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  placeholder="Enter character name"
                />

                <Textarea
                  label="Bio"
                  value={formData.bio}
                  onChange={(e) =>
                    setFormData({ ...formData, bio: e.target.value })
                  }
                  placeholder="Enter character biography"
                  rows={4}
                />

                <div className="grid gap-4 sm:grid-cols-2">
                  <Input
                    label="Age"
                    type="number"
                    min="0"
                    max="150"
                    value={formData.age || ""}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        age: e.target.value ? parseInt(e.target.value) : null,
                      })
                    }
                    placeholder="Age"
                  />

                  <Input
                    label="Location"
                    value={formData.location}
                    onChange={(e) =>
                      setFormData({ ...formData, location: e.target.value })
                    }
                    placeholder="e.g., New York, USA"
                  />
                </div>

                <Input
                  label="Timezone"
                  value={formData.timezone}
                  onChange={(e) =>
                    setFormData({ ...formData, timezone: e.target.value })
                  }
                  placeholder="UTC"
                />

                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-1.5">
                    Interests
                  </label>
                  <div className="flex gap-2">
                    <Input
                      value={interestInput}
                      onChange={(e) => setInterestInput(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addInterest();
                        }
                      }}
                      placeholder="Add interest and press Enter"
                      className="flex-1"
                    />
                    <SecondaryButton
                      type="button"
                      icon={<Plus className="h-4 w-4" />}
                      onClick={addInterest}
                    >
                      Add
                    </SecondaryButton>
                  </div>
                  {formData.interests.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {formData.interests.map((interest) => (
                        <span
                          key={interest}
                          className="inline-flex items-center gap-1 rounded-full bg-[var(--accent-primary)]/10 px-3 py-1 text-xs font-medium text-[var(--accent-primary)] border border-[var(--accent-primary)]/20"
                        >
                          {interest}
                          <button
                            type="button"
                            onClick={() => removeInterest(interest)}
                            className="hover:text-[var(--accent-primary-hover)]"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <Input
                  label="Profile Image URL"
                  type="url"
                  value={formData.profile_image_url}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      profile_image_url: e.target.value,
                    })
                  }
                  placeholder="https://..."
                />
              </FormGroup>
            </SectionCard>
          )}

          {/* Personality Tab */}
          {activeTab === "personality" && (
            <SectionCard title="Personality Traits">
              <FormGroup>
                {formData.personality ? (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Extroversion:{" "}
                        {formData.personality.extroversion.toFixed(1)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={formData.personality.extroversion}
                        onChange={(e) =>
                          updatePersonality({
                            extroversion: parseFloat(e.target.value),
                          })
                        }
                        className="w-full h-2 bg-[var(--bg-surface)] rounded-lg appearance-none cursor-pointer accent-[var(--accent-primary)]"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Creativity: {formData.personality.creativity.toFixed(1)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={formData.personality.creativity}
                        onChange={(e) =>
                          updatePersonality({
                            creativity: parseFloat(e.target.value),
                          })
                        }
                        className="w-full h-2 bg-[var(--bg-surface)] rounded-lg appearance-none cursor-pointer accent-[var(--accent-primary)]"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Humor: {formData.personality.humor.toFixed(1)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={formData.personality.humor}
                        onChange={(e) =>
                          updatePersonality({
                            humor: parseFloat(e.target.value),
                          })
                        }
                        className="w-full h-2 bg-[var(--bg-surface)] rounded-lg appearance-none cursor-pointer accent-[var(--accent-primary)]"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Professionalism:{" "}
                        {formData.personality.professionalism.toFixed(1)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={formData.personality.professionalism}
                        onChange={(e) =>
                          updatePersonality({
                            professionalism: parseFloat(e.target.value),
                          })
                        }
                        className="w-full h-2 bg-[var(--bg-surface)] rounded-lg appearance-none cursor-pointer accent-[var(--accent-primary)]"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                        Authenticity:{" "}
                        {formData.personality.authenticity.toFixed(1)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={formData.personality.authenticity}
                        onChange={(e) =>
                          updatePersonality({
                            authenticity: parseFloat(e.target.value),
                          })
                        }
                        className="w-full h-2 bg-[var(--bg-surface)] rounded-lg appearance-none cursor-pointer accent-[var(--accent-primary)]"
                      />
                    </div>

                    <Select
                      label="Communication Style"
                      options={[
                        { value: "", label: "Select style" },
                        { value: "casual", label: "Casual" },
                        { value: "professional", label: "Professional" },
                        { value: "friendly", label: "Friendly" },
                        { value: "sassy", label: "Sassy" },
                        { value: "witty", label: "Witty" },
                        { value: "thoughtful", label: "Thoughtful" },
                        { value: "energetic", label: "Energetic" },
                        { value: "calm", label: "Calm" },
                      ]}
                      value={formData.personality.communication_style}
                      onChange={(e) =>
                        updatePersonality({
                          communication_style: e.target.value,
                        })
                      }
                    />

                    <Select
                      label="Content Tone"
                      options={[
                        { value: "", label: "Select tone" },
                        { value: "positive", label: "Positive" },
                        { value: "neutral", label: "Neutral" },
                        { value: "edgy", label: "Edgy" },
                        { value: "inspirational", label: "Inspirational" },
                        { value: "humorous", label: "Humorous" },
                        { value: "serious", label: "Serious" },
                      ]}
                      value={formData.personality.content_tone}
                      onChange={(e) =>
                        updatePersonality({ content_tone: e.target.value })
                      }
                    />
                  </>
                ) : (
                  <p className="text-[var(--text-secondary)]">
                    No personality data available. Create personality settings
                    in the character detail page.
                  </p>
                )}
              </FormGroup>
            </SectionCard>
          )}

          {/* Appearance Tab */}
          {activeTab === "appearance" && (
            <SectionCard title="Appearance Settings">
              <FormGroup>
                {formData.appearance ? (
                  <>
                    <Input
                      label="Face Reference Image URL"
                      type="url"
                      value={formData.appearance.face_reference_image_url}
                      onChange={(e) =>
                        updateAppearance({
                          face_reference_image_url: e.target.value,
                        })
                      }
                      placeholder="https://..."
                    />

                    <div className="grid gap-4 sm:grid-cols-2">
                      <Input
                        label="Hair Color"
                        value={formData.appearance.hair_color}
                        onChange={(e) =>
                          updateAppearance({ hair_color: e.target.value })
                        }
                        placeholder="e.g., brown, blonde"
                      />

                      <Input
                        label="Eye Color"
                        value={formData.appearance.eye_color}
                        onChange={(e) =>
                          updateAppearance({ eye_color: e.target.value })
                        }
                        placeholder="e.g., blue, brown"
                      />
                    </div>

                    <Input
                      label="Base Model"
                      value={formData.appearance.base_model}
                      onChange={(e) =>
                        updateAppearance({ base_model: e.target.value })
                      }
                      placeholder="realistic-vision-v6"
                    />
                  </>
                ) : (
                  <p className="text-[var(--text-secondary)]">
                    No appearance data available. Create appearance settings in
                    the character detail page.
                  </p>
                )}
              </FormGroup>
            </SectionCard>
          )}

          {/* Form Actions */}
          <SectionCard>
            <div className="flex items-center justify-between">
              <Link href={`/characters/${characterId}`}>
                <SecondaryButton icon={<ArrowLeft className="h-4 w-4" />}>
                  Cancel
                </SecondaryButton>
              </Link>
              <div className="flex gap-3">
                {activeTab !== "basic" && (
                  <SecondaryButton
                    type="button"
                    onClick={() => {
                      if (activeTab === "personality") setActiveTab("basic");
                      if (activeTab === "appearance")
                        setActiveTab("personality");
                    }}
                  >
                    Previous
                  </SecondaryButton>
                )}
                {activeTab !== "appearance" && (
                  <PrimaryButton
                    type="button"
                    onClick={() => {
                      if (activeTab === "basic") setActiveTab("personality");
                      if (activeTab === "personality")
                        setActiveTab("appearance");
                    }}
                  >
                    Next
                  </PrimaryButton>
                )}
                {activeTab === "appearance" && (
                  <PrimaryButton
                    type="submit"
                    disabled={saving || !formData.name}
                    loading={saving}
                  >
                    Update Character
                  </PrimaryButton>
                )}
              </div>
            </div>
          </SectionCard>
        </form>
      </main>
    </div>
  );
}
