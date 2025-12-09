export type MediaType = 'image' | 'video';
export type MediaSource = 'ai' | 'personal';

export interface MediaItem {
  id: string;
  type: MediaType;
  source: MediaSource;
  url: string;
  thumbnailUrl?: string;
  filename: string;
  size: number;
  width?: number;
  height?: number;
  duration?: number;
  metadata?: {
    prompt?: string;
    characterId?: string;
    generationParams?: Record<string, any>;
    originalFilename?: string;
    uploadedAt?: string;
  };
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export interface MediaFilters {
  type?: MediaType;
  source?: MediaSource;
  characterId?: string;
  tags?: string[];
  dateFrom?: string;
  dateTo?: string;
  search?: string;
}
