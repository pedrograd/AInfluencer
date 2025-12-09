'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react'

interface QualityScores {
  overall: number
  face?: {
    overall: number
    sharpness: number
    symmetry: number
    lighting: number
    expression: number
  }
  technical?: {
    overall: number
    resolution: number
    sharpness: number
    color: number
    composition: number
  }
  realism: number
  artifacts?: {
    detected: boolean
    severity: number
    count: number
  }
  passed?: boolean
}

interface QualityScoreDisplayProps {
  scores: QualityScores
  minScore?: number
}

export function QualityScoreDisplay({ scores, minScore = 8.0 }: QualityScoreDisplayProps) {
  const getScoreColor = (score: number) => {
    if (score >= 9.0) return 'text-green-600 dark:text-green-400'
    if (score >= 8.0) return 'text-blue-600 dark:text-blue-400'
    if (score >= 7.0) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 8.0) {
      return <CheckCircle2 className="h-5 w-5 text-green-600" />
    }
    if (score >= 7.0) {
      return <AlertCircle className="h-5 w-5 text-yellow-600" />
    }
    return <XCircle className="h-5 w-5 text-red-600" />
  }

  const passed = scores.overall >= minScore && (!scores.artifacts || scores.artifacts.severity < 0.2)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Quality Scores
          {getScoreIcon(scores.overall)}
        </CardTitle>
        <CardDescription>
          Automated quality assessment results
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold">Overall Score</span>
            <div className="flex items-center gap-2">
              {getScoreIcon(scores.overall)}
              <span className={`text-2xl font-bold ${getScoreColor(scores.overall)}`}>
                {scores.overall.toFixed(1)}/10
              </span>
            </div>
          </div>
          {scores.passed !== undefined && (
            <div className={`text-sm ${passed ? 'text-green-600' : 'text-red-600'}`}>
              {passed ? '✅ Passed quality check' : '❌ Failed quality check'}
            </div>
          )}
        </div>

        {scores.face && (
          <div className="space-y-2 p-3 bg-muted rounded-lg">
            <div className="font-medium">Face Quality</div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Overall:</span>{' '}
                <span className={getScoreColor(scores.face.overall)}>
                  {scores.face.overall.toFixed(1)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Sharpness:</span>{' '}
                <span className={getScoreColor(scores.face.sharpness)}>
                  {scores.face.sharpness.toFixed(1)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Symmetry:</span>{' '}
                <span className={getScoreColor(scores.face.symmetry)}>
                  {scores.face.symmetry.toFixed(1)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Lighting:</span>{' '}
                <span className={getScoreColor(scores.face.lighting)}>
                  {scores.face.lighting.toFixed(1)}
                </span>
              </div>
            </div>
          </div>
        )}

        {scores.technical && (
          <div className="space-y-2 p-3 bg-muted rounded-lg">
            <div className="font-medium">Technical Quality</div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Overall:</span>{' '}
                <span className={getScoreColor(scores.technical.overall)}>
                  {scores.technical.overall.toFixed(1)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Resolution:</span>{' '}
                <span className={getScoreColor(scores.technical.resolution)}>
                  {scores.technical.resolution.toFixed(1)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Sharpness:</span>{' '}
                <span className={getScoreColor(scores.technical.sharpness)}>
                  {scores.technical.sharpness.toFixed(1)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Color:</span>{' '}
                <span className={getScoreColor(scores.technical.color)}>
                  {scores.technical.color.toFixed(1)}
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-medium">Realism</span>
            <span className={getScoreColor(scores.realism)}>
              {scores.realism.toFixed(1)}/10
            </span>
          </div>
        </div>

        {scores.artifacts && (
          <div className="space-y-2 p-3 bg-muted rounded-lg">
            <div className="font-medium">Artifacts</div>
            <div className="text-sm">
              <div>
                <span className="text-muted-foreground">Detected:</span>{' '}
                <span className={scores.artifacts.detected ? 'text-red-600' : 'text-green-600'}>
                  {scores.artifacts.detected ? 'Yes' : 'No'}
                </span>
              </div>
              {scores.artifacts.detected && (
                <>
                  <div>
                    <span className="text-muted-foreground">Severity:</span>{' '}
                    <span className={getScoreColor(10 - scores.artifacts.severity * 10)}>
                      {(scores.artifacts.severity * 10).toFixed(1)}/10
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Count:</span>{' '}
                    {scores.artifacts.count}
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
