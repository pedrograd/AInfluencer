// Character Management System Types
// Complete type definitions as per Character Management System documentation

export interface Character {
  id: string;
  name: string;
  age?: number;
  description?: string;
  persona?: Persona;
  appearance?: Appearance;
  style?: Style;
  contentPreferences?: ContentPreferences;
  consistencyRules?: ConsistencyRules;
  faceReferences: FaceReference[];
  settings?: Record<string, any>;
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  stats?: CharacterStats;
  faceReferenceCount?: number;
  mediaCount?: number;
}

export interface Persona {
  personality?: {
    traits?: string[];
    voice?: string;
    tone?: string;
  };
  interests?: string[];
  values?: string[];
  backstory?: string;
}

export interface Appearance {
  face?: {
    age?: number;
    ethnicity?: string;
    eyes?: {
      color?: string;
      shape?: string;
      size?: string;
    } | string;
    nose?: string;
    lips?: string;
    jawline?: string;
    cheekbones?: string;
    skin?: {
      tone?: string;
      texture?: string;
    } | string;
    distinctiveFeatures?: string[];
  };
  hair?: {
    color?: string;
    length?: string;
    style?: string;
    texture?: string;
  };
  body?: {
    height?: string;
    build?: string;
    type?: string;
    notableFeatures?: string[];
  };
}

export interface Style {
  photography?: string;
  colorPalette?: {
    primary?: string;
    secondary?: string;
    accent?: string;
  };
  lighting?: string;
  composition?: string;
  mood?: string;
}

export interface ContentPreferences {
  imageTypes?: string[];
  videoTypes?: string[];
  topics?: string[];
  themes?: string[];
}

export interface ConsistencyRules {
  face?: {
    method?: string;
    referenceImages?: string[];
    strength?: number;
    qualityThreshold?: number;
  };
  style?: {
    mustMatch?: boolean;
    colorGrading?: string;
    photographyStyle?: string;
  };
  persona?: {
    voiceConsistency?: string;
    personalityTraits?: string;
    contentAlignment?: string;
  };
}

export interface FaceReference {
  id: string;
  imageUrl?: string;
  filePath?: string;
  fileName?: string;
  thumbnailUrl?: string;
  uploadedAt?: string;
  isPrimary?: boolean;
  width?: number;
  height?: number;
  metadata?: Record<string, any>;
}

export interface CharacterStats {
  totalGenerations: number;
  totalImages: number;
  totalVideos: number;
  faceReferenceCount?: number;
  averageQuality?: number;
  lastUsed?: string;
  lastGeneration?: string;
}

export interface CharacterFormData {
  name: string;
  age?: number;
  description?: string;
  persona?: Persona;
  appearance?: Appearance;
  style?: Style;
  contentPreferences?: ContentPreferences;
  consistencyRules?: ConsistencyRules;
  faceReferences?: File[];
  template?: string;
}

export interface CharacterTemplate {
  name: string;
  persona?: Persona;
  appearance?: Appearance;
  style?: Style;
  contentPreferences?: ContentPreferences;
  consistencyRules?: ConsistencyRules;
}

export interface CharacterExport {
  version: string;
  exportedAt: string;
  character: {
    id: string;
    name: string;
    age?: number;
    description?: string;
    persona?: Persona;
    appearance?: Appearance;
    style?: Style;
    contentPreferences?: ContentPreferences;
    consistencyRules?: ConsistencyRules;
    settings?: Record<string, any>;
    metadata?: Record<string, any>;
    createdAt?: string;
    updatedAt?: string;
  };
  faceReferences: Array<{
    id: string;
    fileName: string;
    width?: number;
    height?: number;
    metadata?: Record<string, any>;
  }>;
  styleGuide?: Style;
}
