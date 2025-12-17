"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";

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
  const [activeTab, setActiveTab] = useState<"basic" | "personality" | "appearance">("basic");
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
      const response = await apiPost<{ success: boolean; data: { id: string } }>(
        "/api/characters",
        {
          name: formData.name,
          bio: formData.bio || null,
          age: formData.age || null,
          location: formData.location || null,
          timezone: formData.timezone,
          interests: formData.interests.length > 0 ? formData.interests : null,
          profile_image_url: formData.profile_image_url || null,
          personality: personalityPayload,
          appearance: appearancePayload,
        }
      );

      if (response.success) {
        router.push(`/characters/${response.data.id}`);
      } else {
        setError("Failed to create character");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create character");
    } finally {
      setLoading(false);
    }
  };

  const addInterest = () => {
    if (interestInput.trim() && !formData.interests.includes(interestInput.trim())) {
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
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <main className="mx-auto w-full max-w-4xl px-4 sm:px-6 py-8 sm:py-14">
        <div className="mb-6 sm:mb-8">
          <Link href="/" className="text-xs sm:text-sm text-zinc-600 hover:text-zinc-900">
            ← Back to Dashboard
          </Link>
          <h1 className="mt-3 sm:mt-4 text-2xl sm:text-3xl font-semibold tracking-tight">Create New Character</h1>
          <p className="mt-2 sm:mt-3 text-xs sm:text-sm leading-6 text-zinc-600">
            Create a new AI influencer character with unique personality and appearance.
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            <strong>Error:</strong> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Tabs */}
          <div className="border-b border-zinc-200 overflow-x-auto">
            <nav className="-mb-px flex space-x-4 sm:space-x-8">
              <button
                type="button"
                onClick={() => setActiveTab("basic")}
                className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                  activeTab === "basic"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-zinc-500 hover:border-zinc-300 hover:text-zinc-700"
                }`}
              >
                Basic Info
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("personality")}
                className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                  activeTab === "personality"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-zinc-500 hover:border-zinc-300 hover:text-zinc-700"
                }`}
              >
                Personality
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("appearance")}
                className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                  activeTab === "appearance"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-zinc-500 hover:border-zinc-300 hover:text-zinc-700"
                }`}
              >
                Appearance
              </button>
            </nav>
          </div>

          {/* Basic Info Tab */}
          {activeTab === "basic" && (
            <div className="space-y-6 rounded-xl border border-zinc-200 bg-white p-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-zinc-700">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Enter character name"
                />
              </div>

              <div>
                <label htmlFor="bio" className="block text-sm font-medium text-zinc-700">
                  Bio
                </label>
                <textarea
                  id="bio"
                  rows={4}
                  value={formData.bio}
                  onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Enter character biography"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="age" className="block text-sm font-medium text-zinc-700">
                    Age
                  </label>
                  <input
                    type="number"
                    id="age"
                    min="0"
                    max="150"
                    value={formData.age || ""}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        age: e.target.value ? parseInt(e.target.value) : null,
                      })
                    }
                    className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="Age"
                  />
                </div>

                <div>
                  <label htmlFor="location" className="block text-sm font-medium text-zinc-700">
                    Location
                  </label>
                  <input
                    type="text"
                    id="location"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="e.g., New York, USA"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="timezone" className="block text-sm font-medium text-zinc-700">
                  Timezone
                </label>
                <input
                  type="text"
                  id="timezone"
                  value={formData.timezone}
                  onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="UTC"
                />
              </div>

              <div>
                <label htmlFor="interests" className="block text-sm font-medium text-zinc-700">
                  Interests
                </label>
                <div className="mt-1 flex gap-2">
                  <input
                    type="text"
                    id="interests"
                    value={interestInput}
                    onChange={(e) => setInterestInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addInterest();
                      }
                    }}
                    className="block flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="Add interest and press Enter"
                  />
                  <button
                    type="button"
                    onClick={addInterest}
                    className="rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
                  >
                    Add
                  </button>
                </div>
                {formData.interests.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {formData.interests.map((interest) => (
                      <span
                        key={interest}
                        className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800"
                      >
                        {interest}
                        <button
                          type="button"
                          onClick={() => removeInterest(interest)}
                          className="hover:text-blue-900"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label htmlFor="profile_image_url" className="block text-sm font-medium text-zinc-700">
                  Profile Image URL
                </label>
                <input
                  type="url"
                  id="profile_image_url"
                  value={formData.profile_image_url}
                  onChange={(e) => setFormData({ ...formData, profile_image_url: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="https://..."
                />
              </div>
            </div>
          )}

          {/* Personality Tab */}
          {activeTab === "personality" && (
            <div className="space-y-6 rounded-xl border border-zinc-200 bg-white p-6">
              <div>
                <label className="block text-sm font-medium text-zinc-700">
                  Extroversion: {personality.extroversion.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={personality.extroversion}
                  onChange={(e) =>
                    updatePersonality({ extroversion: parseFloat(e.target.value) })
                  }
                  className="mt-1 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700">
                  Creativity: {personality.creativity.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={personality.creativity}
                  onChange={(e) =>
                    updatePersonality({ creativity: parseFloat(e.target.value) })
                  }
                  className="mt-1 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700">
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
                  className="mt-1 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700">
                  Professionalism: {personality.professionalism.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={personality.professionalism}
                  onChange={(e) =>
                    updatePersonality({ professionalism: parseFloat(e.target.value) })
                  }
                  className="mt-1 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700">
                  Authenticity: {personality.authenticity.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={personality.authenticity}
                  onChange={(e) =>
                    updatePersonality({ authenticity: parseFloat(e.target.value) })
                  }
                  className="mt-1 w-full"
                />
              </div>

              <div>
                <label htmlFor="communication_style" className="block text-sm font-medium text-zinc-700">
                  Communication Style
                </label>
                <select
                  id="communication_style"
                  value={personality.communication_style}
                  onChange={(e) =>
                    updatePersonality({ communication_style: e.target.value })
                  }
                  className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Select style</option>
                  <option value="casual">Casual</option>
                  <option value="professional">Professional</option>
                  <option value="friendly">Friendly</option>
                  <option value="sassy">Sassy</option>
                  <option value="witty">Witty</option>
                  <option value="thoughtful">Thoughtful</option>
                  <option value="energetic">Energetic</option>
                  <option value="calm">Calm</option>
                </select>
              </div>

              <div>
                <label htmlFor="content_tone" className="block text-sm font-medium text-zinc-700">
                  Content Tone
                </label>
                <select
                  id="content_tone"
                  value={personality.content_tone}
                  onChange={(e) =>
                    updatePersonality({ content_tone: e.target.value })
                  }
                  className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Select tone</option>
                  <option value="positive">Positive</option>
                  <option value="neutral">Neutral</option>
                  <option value="edgy">Edgy</option>
                  <option value="inspirational">Inspirational</option>
                  <option value="humorous">Humorous</option>
                  <option value="serious">Serious</option>
                </select>
              </div>
            </div>
          )}

          {/* Appearance Tab */}
          {activeTab === "appearance" && (
            <div className="space-y-6 rounded-xl border border-zinc-200 bg-white p-6">
              <div>
                <label htmlFor="face_reference_image_url" className="block text-sm font-medium text-zinc-700">
                  Face Reference Image URL
                </label>
                <input
                  type="url"
                  id="face_reference_image_url"
                  value={appearance.face_reference_image_url}
                  onChange={(e) =>
                    updateAppearance({ face_reference_image_url: e.target.value })
                  }
                  className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="https://..."
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="hair_color" className="block text-sm font-medium text-zinc-700">
                    Hair Color
                  </label>
                  <input
                    type="text"
                    id="hair_color"
                    value={appearance.hair_color}
                    onChange={(e) => updateAppearance({ hair_color: e.target.value })}
                    className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="e.g., brown, blonde"
                  />
                </div>

                <div>
                  <label htmlFor="eye_color" className="block text-sm font-medium text-zinc-700">
                    Eye Color
                  </label>
                  <input
                    type="text"
                    id="eye_color"
                    value={appearance.eye_color}
                    onChange={(e) => updateAppearance({ eye_color: e.target.value })}
                    className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="e.g., blue, brown"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="base_model" className="block text-sm font-medium text-zinc-700">
                  Base Model
                </label>
                <input
                  type="text"
                  id="base_model"
                    value={appearance.base_model}
                    onChange={(e) => updateAppearance({ base_model: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="realistic-vision-v6"
                />
              </div>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex items-center justify-between rounded-xl border border-zinc-200 bg-white p-6">
            <Link
              href="/"
              className="rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
            >
              Cancel
            </Link>
            <div className="flex gap-3">
              {activeTab !== "basic" && (
                <button
                  type="button"
                  onClick={() => {
                    if (activeTab === "personality") setActiveTab("basic");
                    if (activeTab === "appearance") setActiveTab("personality");
                  }}
                  className="rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
                >
                  Previous
                </button>
              )}
              {activeTab !== "appearance" && (
                <button
                  type="button"
                  onClick={() => {
                    if (activeTab === "basic") setActiveTab("personality");
                    if (activeTab === "personality") setActiveTab("appearance");
                  }}
                  className="rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
                >
                  Next
                </button>
              )}
              {activeTab === "appearance" && (
                <button
                  type="submit"
                  disabled={loading || !formData.name}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-zinc-400"
                >
                  {loading ? "Creating..." : "Create Character"}
                </button>
              )}
            </div>
          </div>
        </form>
      </main>
    </div>
  );
}

