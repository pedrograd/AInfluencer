export type FaceConsistencyMethod = 'ip_adapter' | 'instantid' | 'faceid' | 'lora';

export interface FaceConsistencyConfig {
  enabled: boolean;
  method: FaceConsistencyMethod;
  strength: number; // 0.0 to 1.0
  faceReferencePath?: string;
  multipleReferences?: string[];
  loraName?: string; // Required for LoRA method
  ipMethod?: string; // For IP-Adapter variants
  controlnetStrength?: number; // For InstantID
  ipAdapterScale?: number; // For InstantID
}

export interface FaceQualityResult {
  quality_score: number;
  width: number;
  height: number;
  aspect_ratio: number;
  brightness: number;
  face_detected: boolean;
  face_quality?: number;
  issues: string[];
  recommendations: string[];
  is_valid: boolean;
  is_optimal: boolean;
}

export interface FaceSimilarityResult {
  similarity: number;
  target_met: boolean;
  target: number;
}

export interface FaceConsistencyTestResult {
  average: number;
  minimum: number;
  maximum: number;
  std_dev: number;
  count: number;
  similarities: number[];
  passed: boolean;
  target_met: {
    average_target: boolean;
    minimum_target: boolean;
    std_dev_target: boolean;
  };
}

export interface FaceConsistencyMethodInfo {
  name: string;
  consistency: number;
  speed: string;
  setup_difficulty: string;
  cost: string;
  best_for: string;
  available: boolean;
}

export interface PostProcessingConfig {
  enabled: boolean;
  upscale: boolean;
  upscale_factor: number;
  face_restoration: boolean;
  color_correction: boolean;
  noise_reduction: boolean;
  remove_metadata: boolean;
  quality_optimization: boolean;
  output_format: 'PNG' | 'JPG' | 'WEBP';
  quality: number;
}

export interface AntiDetectionConfig {
  enabled: boolean;
  remove_metadata: boolean;
  add_imperfections: boolean;
  vary_quality: boolean;
  remove_ai_signatures: boolean;
  add_realistic_noise: boolean;
  normalize_colors: boolean;
}

export interface QualityCheckConfig {
  enabled: boolean;
  min_score: number;
}

export interface GenerationParams {
  prompt: string;
  negativePrompt?: string;
  faceReference?: string;
  characterId?: string;
  cfg: number;
  steps: number;
  seed?: number;
  width: number;
  height: number;
  sampler: string;
  qualityPreset: 'fast' | 'balanced' | 'ultra';
  batchCount: number;
  faceConsistency?: FaceConsistencyConfig;
  postProcessing?: PostProcessingConfig;
  antiDetection?: AntiDetectionConfig;
  qualityCheck?: QualityCheckConfig;
}

export interface VideoGenerationParams extends GenerationParams {
  duration: number;
  fps: number;
  motionStrength: number;
}

export interface GenerationProgress {
  promptId: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  currentStep?: number;
  totalSteps?: number;
  preview?: string;
  error?: string;
}

export interface GenerationResult {
  id: string;
  promptId: string;
  imageUrl: string;
  thumbnailUrl?: string;
  mediaId?: string;
  metadata: {
    prompt: string;
    negativePrompt?: string;
    cfg: number;
    steps: number;
    seed: number;
    width: number;
    height: number;
    sampler: string;
    model: string;
    timestamp: string;
  };
  createdAt: string;
}
