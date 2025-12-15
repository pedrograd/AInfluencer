"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";

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
    personality: null,
    appearance: null,
  });
  const [interestInput, setInterestInput] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
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
          personality: formData.personality,
          appearance: formData.appearance,
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
      <main className="mx-auto w-full max-w-4xl px-6 py-14">
        <div className="mb-8">
          <Link href="/" className="text-sm text-zinc-600 hover:text-zinc-900">
            ← Back to Dashboard
          </Link>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight">Create New Character</h1>
          <p className="mt-3 text-sm leading-6 text-zinc-600">
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
          <div className="border-b border-zinc-200">
            <nav className="-mb-px flex space-x-8">
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
                  Extroversion: {formData.personality?.extroversion.toFixed(1) || "0.5"}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.personality?.extroversion || 0.5}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      personality: {
                        extroversion: parseFloat(e.target.value),
                        creativity: formData.personality?.creativity || 0.5,
                        humor: formData.personality?.humor || 0.5,
                        professionalism: formData.personality?.professionalism || 0.5,
                        authenticity: formData.personality?.authenticity || 0.5,
                        communication_style: formData.personality?.communication_style || "",
                        preferred_topics: formData.personality?.preferred_topics || [],
                        content_tone: formData.personality?.content_tone || "",
                        temperature: formData.personality?.temperature || 0.7,
                      },
                    })
                  }
                  className="mt-1 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700">
                  Creativity: {formData.personality?.creativity.toFixed(1) || "0.5"}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.personality?.creativity || 0.5}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      personality: {
                        extroversion: formData.personality?.extroversion || 0.5,
                        creativity: parseFloat(e.target.value),
                        humor: formData.personality?.humor || 0.5,
                        professionalism: formData.personality?.professionalism || 0.5,
                        authenticity: formData.personality?.authenticity || 0.5,
                        communication_style: formData.personality?.communication_style || "",
                        preferred_topics: formData.personality?.preferred_topics || [],
                        content_tone: formData.personality?.content_tone || "",
                        temperature: formData.personality?.temperature || 0.7,
                      },
                    })
                  }
                  className="mt-1 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700">
                  Humor: {formData.personality?.humor.toFixed(1) || "0.5"}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.personality?.humor || 0.5}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      personality: {
                        extroversion: formData.personality?.extroversion || 0.5,
                        creativity: formData.personality?.creativity || 0.5,
                        humor: parseFloat(e.target.value),
                        professionalism: formData.personality?.professionalism || 0.5,
                        authenticity: formData.personality?.authenticity || 0.5,
                        communication_style: formData.personality?.communication_style || "",
                        preferred_topics: formData.personality?.preferred_topics || [],
                        content_tone: formData.personality?.content_tone || "",
                        temperature: formData.personality?.temperature || 0.7,
                      },
                    })
                  }
                  className="mt-1 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700">
                  Professionalism: {formData.personality?.professionalism.toFixed(1) || "0.5"}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.personality?.professionalism || 0.5}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      personality: {
                        extroversion: formData.personality?.extroversion || 0.5,
                        creativity: formData.personality?.creativity || 0.5,
                        humor: formData.personality?.humor || 0.5,
                        professionalism: parseFloat(e.target.value),
                        authenticity: formData.personality?.authenticity || 0.5,
                        communication_style: formData.personality?.communication_style || "",
                        preferred_topics: formData.personality?.preferred_topics || [],
                        content_tone: formData.personality?.content_tone || "",
                        temperature: formData.personality?.temperature || 0.7,
                      },
                    })
                  }
                  className="mt-1 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700">
                  Authenticity: {formData.personality?.authenticity.toFixed(1) || "0.5"}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.personality?.authenticity || 0.5}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      personality: {
                        extroversion: formData.personality?.extroversion || 0.5,
                        creativity: formData.personality?.creativity || 0.5,
                        humor: formData.personality?.humor || 0.5,
                        professionalism: formData.personality?.professionalism || 0.5,
                        authenticity: parseFloat(e.target.value),
                        communication_style: formData.personality?.communication_style || "",
                        preferred_topics: formData.personality?.preferred_topics || [],
                        content_tone: formData.personality?.content_tone || "",
                        temperature: formData.personality?.temperature || 0.7,
                      },
                    })
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
                  value={formData.personality?.communication_style || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      personality: {
                        extroversion: formData.personality?.extroversion || 0.5,
                        creativity: formData.personality?.creativity || 0.5,
                        humor: formData.personality?.humor || 0.5,
                        professionalism: formData.personality?.professionalism || 0.5,
                        authenticity: formData.personality?.authenticity || 0.5,
                        communication_style: e.target.value,
                        preferred_topics: formData.personality?.preferred_topics || [],
                        content_tone: formData.personality?.content_tone || "",
                        temperature: formData.personality?.temperature || 0.7,
                      },
                    })
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
                  value={formData.personality?.content_tone || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      personality: {
                        extroversion: formData.personality?.extroversion || 0.5,
                        creativity: formData.personality?.creativity || 0.5,
                        humor: formData.personality?.humor || 0.5,
                        professionalism: formData.personality?.professionalism || 0.5,
                        authenticity: formData.personality?.authenticity || 0.5,
                        communication_style: formData.personality?.communication_style || "",
                        preferred_topics: formData.personality?.preferred_topics || [],
                        content_tone: e.target.value,
                        temperature: formData.personality?.temperature || 0.7,
                      },
                    })
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
                  value={formData.appearance?.face_reference_image_url || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      appearance: {
                        face_reference_image_url: e.target.value,
                        hair_color: formData.appearance?.hair_color || "",
                        eye_color: formData.appearance?.eye_color || "",
                        base_model: formData.appearance?.base_model || "realistic-vision-v6",
                      },
                    })
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
                    value={formData.appearance?.hair_color || ""}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        appearance: {
                          face_reference_image_url: formData.appearance?.face_reference_image_url || "",
                          hair_color: e.target.value,
                          eye_color: formData.appearance?.eye_color || "",
                          base_model: formData.appearance?.base_model || "realistic-vision-v6",
                        },
                      })
                    }
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
                    value={formData.appearance?.eye_color || ""}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        appearance: {
                          face_reference_image_url: formData.appearance?.face_reference_image_url || "",
                          hair_color: formData.appearance?.hair_color || "",
                          eye_color: e.target.value,
                          base_model: formData.appearance?.base_model || "realistic-vision-v6",
                        },
                      })
                    }
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
                  value={formData.appearance?.base_model || "realistic-vision-v6"}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      appearance: {
                        face_reference_image_url: formData.appearance?.face_reference_image_url || "",
                        hair_color: formData.appearance?.hair_color || "",
                        eye_color: formData.appearance?.eye_color || "",
                        base_model: e.target.value,
                      },
                    })
                  }
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

