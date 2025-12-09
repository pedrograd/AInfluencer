export interface PracticeViolation {
  category: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  practice: string
  description: string
  location: string
  suggestion: string
  timestamp?: string
}

export interface PracticeCheck {
  practice: string
  passed: boolean
  score: number
  violations_count?: number
  violations?: PracticeViolation[]
  details?: Record<string, any>
}

export interface PracticeReport {
  timestamp: string
  overall_score: number
  category_scores: Record<string, number>
  checks: PracticeCheck[]
  violations: PracticeViolation[]
  recommendations: string[]
  metadata?: {
    total_checks?: number
    total_violations?: number
    critical_count?: number
    high_count?: number
  }
}

export interface BestPracticesConfig {
  min_quality_score: number
  min_face_consistency: number
  require_metadata_removal: boolean
  require_post_processing: boolean
  enable_automated_checks: boolean
}
