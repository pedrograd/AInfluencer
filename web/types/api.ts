export interface ComfyUIWorkflow {
  [key: string]: any;
}

export interface ComfyUIQueueResponse {
  prompt_id: string;
}

export interface ComfyUIHistoryItem {
  prompt: any[];
  outputs: Record<string, any>;
}

export interface ComfyUIWebSocketMessage {
  type: string;
  data?: any;
  prompt_id?: string;
  node?: string;
  value?: number;
  max?: number;
  status?: {
    status_str: string;
    completed: number;
    total: number;
  };
}

export interface APIError {
  message: string;
  code?: string;
  details?: any;
}

// Platform Integration Types
export interface PlatformAccount {
  id: string;
  platform: 'instagram' | 'twitter' | 'facebook' | 'telegram' | 'onlyfans' | 'youtube';
  username: string;
  display_name?: string;
  is_active: boolean;
  last_used_at?: string;
  created_at?: string;
}

export interface PlatformPost {
  id: string;
  account_id: string;
  platform: string;
  media_id?: string;
  post_type: string;
  caption: string;
  status: 'pending' | 'scheduled' | 'published' | 'failed';
  platform_post_id?: string;
  scheduled_at?: string;
  published_at?: string;
  failed_at?: string;
  error_message?: string;
  retry_count: number;
  metadata?: Record<string, any>;
  created_at?: string;
}

export interface PlatformRateLimit {
  platform: string;
  action: string;
  can_make_request: boolean;
  wait_time: number;
  limits: {
    max: number;
    window: number;
  };
}
