export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GET ${path} failed: ${res.status} ${text}`);
  }
  return (await res.json()) as T;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`POST ${path} failed: ${res.status} ${text}`);
  }
  return (await res.json()) as T;
}

export async function apiPut<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`PUT ${path} failed: ${res.status} ${text}`);
  }
  return (await res.json()) as T;
}

export async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`DELETE ${path} failed: ${res.status} ${text}`);
  }
  return (await res.json()) as T;
}

// Character Image Style Types
export type ImageStyle = {
  id: string;
  character_id: string;
  name: string;
  description: string | null;
  prompt_suffix: string | null;
  prompt_prefix: string | null;
  negative_prompt_addition: string | null;
  checkpoint: string | null;
  sampler_name: string | null;
  scheduler: string | null;
  steps: number | null;
  cfg: number | null;
  width: number | null;
  height: number | null;
  style_keywords: string[] | null;
  display_order: number;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
};

export type ImageStyleCreate = {
  name: string;
  description?: string | null;
  prompt_suffix?: string | null;
  prompt_prefix?: string | null;
  negative_prompt_addition?: string | null;
  checkpoint?: string | null;
  sampler_name?: string | null;
  scheduler?: string | null;
  steps?: number | null;
  cfg?: number | null;
  width?: number | null;
  height?: number | null;
  style_keywords?: string[] | null;
  display_order?: number;
  is_active?: boolean;
  is_default?: boolean;
};

export type ImageStyleUpdate = Partial<ImageStyleCreate>;

export type ImageStyleListResponse = {
  success: boolean;
  data: ImageStyle[];
  total?: number;
};

export type ImageStyleResponse = {
  success: boolean;
  data: ImageStyle;
};

// Character Image Style API Functions
export async function getCharacterStyles(
  characterId: string,
  isActive?: boolean
): Promise<ImageStyle[]> {
  const params = new URLSearchParams();
  if (isActive !== undefined) {
    params.append("is_active", String(isActive));
  }
  const path = `/api/characters/${characterId}/styles${params.toString() ? `?${params.toString()}` : ""}`;
  const response = await apiGet<ImageStyleListResponse>(path);
  return response.data;
}

export async function getCharacterStyle(
  characterId: string,
  styleId: string
): Promise<ImageStyle> {
  const response = await apiGet<ImageStyleResponse>(
    `/api/characters/${characterId}/styles/${styleId}`
  );
  return response.data;
}

export async function createCharacterStyle(
  characterId: string,
  styleData: ImageStyleCreate
): Promise<ImageStyle> {
  const response = await apiPost<ImageStyleResponse>(
    `/api/characters/${characterId}/styles`,
    styleData
  );
  return response.data;
}

export async function updateCharacterStyle(
  characterId: string,
  styleId: string,
  styleData: ImageStyleUpdate
): Promise<ImageStyle> {
  const response = await apiPut<ImageStyleResponse>(
    `/api/characters/${characterId}/styles/${styleId}`,
    styleData
  );
  return response.data;
}

export async function deleteCharacterStyle(
  characterId: string,
  styleId: string
): Promise<void> {
  await apiDelete<{ success: boolean }>(
    `/api/characters/${characterId}/styles/${styleId}`
  );
}

// White-label Configuration Types
export type WhiteLabelConfig = {
  app_name: string;
  app_description: string | null;
  logo_url: string | null;
  favicon_url: string | null;
  primary_color: string;
  secondary_color: string;
  is_active: boolean;
};

export type WhiteLabelConfigUpdate = {
  app_name?: string | null;
  app_description?: string | null;
  logo_url?: string | null;
  favicon_url?: string | null;
  primary_color?: string | null;
  secondary_color?: string | null;
  is_active?: boolean | null;
};

// White-label API Functions
export async function getWhiteLabelConfig(): Promise<WhiteLabelConfig> {
  return apiGet<WhiteLabelConfig>("/api/white-label");
}

export async function updateWhiteLabelConfig(
  config: WhiteLabelConfigUpdate
): Promise<WhiteLabelConfig> {
  return apiPut<WhiteLabelConfig>("/api/white-label", config);
}

// Marketplace Template Types
export type CharacterTemplate = {
  id: string;
  creator_id: string | null;
  name: string;
  description: string | null;
  category: string | null;
  tags: string[] | null;
  preview_image_url: string | null;
  is_featured: boolean;
  is_public: boolean;
  download_count: number;
  rating: number | null;
  rating_count: number;
  created_at: string;
  updated_at: string;
  creator_name?: string | null;
};

export type TemplateDetail = CharacterTemplate & {
  template_data: {
    character: {
      name: string;
      bio: string | null;
      age: number | null;
      location: string | null;
      timezone: string;
      interests: string[] | null;
      profile_image_url: string | null;
    };
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
};

export type TemplateListResponse = {
  success: boolean;
  data: CharacterTemplate[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
};

export type TemplateDetailResponse = {
  success: boolean;
  data: TemplateDetail;
};

export type TemplatePublishRequest = {
  character_id: string;
  name: string;
  description?: string | null;
  category?: string | null;
  tags?: string[] | null;
  preview_image_url?: string | null;
  is_public?: boolean;
};

export type TemplateUseRequest = {
  template_id: string;
  name?: string | null;
  team_id?: string | null;
};

// Marketplace API Functions
export async function listTemplates(params?: {
  category?: string;
  search?: string;
  featured_only?: boolean;
  limit?: number;
  offset?: number;
}): Promise<TemplateListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.category) searchParams.set("category", params.category);
  if (params?.search) searchParams.set("search", params.search);
  if (params?.featured_only) searchParams.set("featured_only", "true");
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  if (params?.offset) searchParams.set("offset", params.offset.toString());
  
  const query = searchParams.toString();
  return apiGet<TemplateListResponse>(`/api/marketplace${query ? `?${query}` : ""}`);
}

export async function getTemplate(templateId: string): Promise<TemplateDetailResponse> {
  return apiGet<TemplateDetailResponse>(`/api/marketplace/${templateId}`);
}

export async function publishTemplate(
  request: TemplatePublishRequest
): Promise<{ success: boolean; data: any; message: string }> {
  return apiPost<{ success: boolean; data: any; message: string }>(
    "/api/marketplace/publish",
    request
  );
}

export async function useTemplate(
  templateId: string,
  request?: TemplateUseRequest
): Promise<{ success: boolean; data: any; message: string }> {
  return apiPost<{ success: boolean; data: any; message: string }>(
    `/api/marketplace/${templateId}/use`,
    request || { template_id: templateId }
  );
}
