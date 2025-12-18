"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";
import {
  PageHeader,
  SectionCard,
  PrimaryButton,
  SecondaryButton,
  Input,
  Textarea,
  Select,
  FormGroup,
  Alert,
  ErrorBanner,
} from "@/components/ui";
import { ArrowLeft, Plus, X } from "lucide-react";

type PersonalityProfile = {
  extroversion: number;
  creativity: number;
  humor: number;
  professionalism: number;
  authenticity: number;
  communication_style: string;
  preferred_topics: string[];
  content_tone: string;
  temperature: number;
};

type AppearanceProfile = {
  face_reference_image_url: string;
  hair_color: string;
  eye_color: string;
  base_model: string;
};

type CharacterFormData = {
  name: string;
  bio: string;
  age: number | null;
  location: string;
  timezone: string;
  interests: string[];
  profile_image_url: string;
  personality: PersonalityProfile;
  appearance: AppearanceProfile;
};

const defaultPersonality: PersonalityProfile = {
  extroversion: 0.5,
  creativity: 0.5,
  humor: 0.5,
  professionalism: 0.5,
  authenticity: 0.5,
  communication_style: "",
  preferred_topics: [],
  content_tone: "",
  temperature: 0.7,
};

const defaultAppearance: AppearanceProfile = {
  face_reference_image_url: "",
  hair_color: "",
  eye_color: "",
  base_model: "realistic-vision-v6",
};

const cloneDefaultPersonality = (): PersonalityProfile => ({
  ...defaultPersonality,
  preferred_topics: [...defaultPersonality.preferred_topics],
});

const cloneDefaultAppearance = (): AppearanceProfile => ({
  ...defaultAppearance,
});

const normalizePersonalityPayload = (
  personality: PersonalityProfile
): PersonalityProfile | null => {
  const hasCustomValues =
    personality.communication_style ||
    personality.content_tone ||
    personality.preferred_topics.length > 0 ||
    personality.extroversion !== defaultPersonality.extroversion ||
    personality.creativity !== defaultPersonality.creativity ||
    personality.humor !== defaultPersonality.humor ||
    personality.professionalism !== defaultPersonality.professionalism ||
    personality.authenticity !== defaultPersonality.authenticity ||
    personality.temperature !== defaultPersonality.temperature;

  if (!hasCustomValues) {
    return null;
  }

  return {
    ...personality,
    preferred_topics: personality.preferred_topics.length
      ? personality.preferred_topics
      : [],
  };
};

const normalizeAppearancePayload = (
  appearance: AppearanceProfile
): AppearanceProfile | null => {
  const hasCustomValues =
    appearance.face_reference_image_url ||
    appearance.hair_color ||
    appearance.eye_color ||
    appearance.base_model !== defaultAppearance.base_model;

  return hasCustomValues ? appearance : null;
};

export default function CreateCharacterPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<
    "basic" | "personality" | "appearance"
  >("basic");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<CharacterFormData>({
    name: "",
    bio: "",
    age: null,
    location: "",
    timezone: "UTC",
    interests: [],
    profile_image_url: "",
    personality: cloneDefaultPersonality(),
    appearance: cloneDefaultAppearance(),
  });
  const [interestInput, setInterestInput] = useState("");

  const personality = formData.personality;
  const appearance = formData.appearance;

  const updatePersonality = (updates: Partial<PersonalityProfile>) =>
    setFormData((prev) => ({
      ...prev,
      personality: { ...prev.personality, ...updates },
    }));

  const updateAppearance = (updates: Partial<AppearanceProfile>) =>
    setFormData((prev) => ({
      ...prev,
      appearance: { ...prev.appearance, ...updates },
    }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const personalityPayload = normalizePersonalityPayload(personality);
      const appearancePayload = normalizeAppearancePayload(appearance);
      const response = await apiPost<{
        success: boolean;
        data: { id: string };
      }>("/api/characters", {
        name: formData.name,
        bio: formData.bio || null,
        age: formData.age || null,
        location: formData.location || null,
        timezone: formData.timezone,
        interests: formData.interests.length > 0 ? formData.interests : null,
        profile_image_url: formData.profile_image_url || null,
        personality: personalityPayload,
        appearance: appearancePayload,
      });

      if (response.success) {
        router.push(`/characters/${response.data.id}`);
      } else {
        setError("Failed to create character");
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create character"
      );
    } finally {
      setLoading(false);
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

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <main className="container mx-auto px-6 py-8">
        <PageHeader
          title="Create New Character"
          description="Create a new AI influencer character with unique personality and appearance."
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
              title="Error creating character"
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
                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                    Extroversion: {personality.extroversion.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={personality.extroversion}
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
                    Creativity: {personality.creativity.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={personality.creativity}
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
                    Humor: {personality.humor.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={personality.humor}
                    onChange={(e) =>
                      updatePersonality({ humor: parseFloat(e.target.value) })
                    }
                    className="w-full h-2 bg-[var(--bg-surface)] rounded-lg appearance-none cursor-pointer accent-[var(--accent-primary)]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                    Professionalism: {personality.professionalism.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={personality.professionalism}
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
                    Authenticity: {personality.authenticity.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={personality.authenticity}
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
                  value={personality.communication_style}
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
                  value={personality.content_tone}
                  onChange={(e) =>
                    updatePersonality({ content_tone: e.target.value })
                  }
                />
              </FormGroup>
            </SectionCard>
          )}

          {/* Appearance Tab */}
          {activeTab === "appearance" && (
            <SectionCard title="Appearance Settings">
              <FormGroup>
                <Input
                  label="Face Reference Image URL"
                  type="url"
                  value={appearance.face_reference_image_url}
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
                    value={appearance.hair_color}
                    onChange={(e) =>
                      updateAppearance({ hair_color: e.target.value })
                    }
                    placeholder="e.g., brown, blonde"
                  />

                  <Input
                    label="Eye Color"
                    value={appearance.eye_color}
                    onChange={(e) =>
                      updateAppearance({ eye_color: e.target.value })
                    }
                    placeholder="e.g., blue, brown"
                  />
                </div>

                <Input
                  label="Base Model"
                  value={appearance.base_model}
                  onChange={(e) =>
                    updateAppearance({ base_model: e.target.value })
                  }
                  placeholder="realistic-vision-v6"
                />
              </FormGroup>
            </SectionCard>
          )}

          {/* Form Actions */}
          <SectionCard>
            <div className="flex items-center justify-between">
              <Link href="/characters">
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
                    disabled={loading || !formData.name}
                    loading={loading}
                  >
                    Create Character
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
