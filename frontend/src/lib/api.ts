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
