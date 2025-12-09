'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, BarChart3, CheckCircle2 } from 'lucide-react'
import { Progress } from '@/components/ui/progress'

interface QualityScores {
  overall: number
  sharpness: number
  contrast: number
  color: number
  artifacts: number
  face_quality?: number
}

export function QualityScoring() {
  const [imagePath, setImagePath] = useState('')
  const [processing, setProcessing] = useState(false)
  const [scores, setScores] = useState<QualityScores | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleScore = async () => {
    if (!imagePath) {
      setError('Please provide an image path')
      return
    }

    setProcessing(true)
    setError(null)
    setScores(null)

    try {
      const response = await backendAPI.automatedQualityScoring(imagePath)
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const errorMessage = (response as any)?.error?.message

      if (success) {
        setScores(data)
      } else {
        setError(errorMessage || 'Quality scoring failed')
      }
    } catch (err: any) {
      setError(err.message || 'Quality scoring failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5" />
          <span>Automated Quality Scoring</span>
        </CardTitle>
        <CardDescription>
          Get comprehensive quality scores (0-10 scale) for your images
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Image Path</label>
          <Input
            value={imagePath}
            onChange={(e) => setImagePath(e.target.value)}
            placeholder="/path/to/image.png"
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-sm text-red-800 dark:text-red-200">
            {error}
          </div>
        )}

        {scores && (
          <div className="space-y-3">
            <div className="p-4 bg-muted rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Overall Score</span>
                <span className="text-2xl font-bold">{scores.overall.toFixed(1)}/10</span>
              </div>
              <Progress value={scores.overall * 10} className="h-2" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Sharpness</span>
                  <span>{scores.sharpness.toFixed(1)}</span>
                </div>
                <Progress value={scores.sharpness * 10} className="h-1" />
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Contrast</span>
                  <span>{scores.contrast.toFixed(1)}</span>
                </div>
                <Progress value={scores.contrast * 10} className="h-1" />
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Color</span>
                  <span>{scores.color.toFixed(1)}</span>
                </div>
                <Progress value={scores.color * 10} className="h-1" />
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Artifacts</span>
                  <span>{scores.artifacts.toFixed(1)}</span>
                </div>
                <Progress value={scores.artifacts * 10} className="h-1" />
              </div>
            </div>

            {scores.overall >= 8.0 && (
              <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
                <div className="flex items-center space-x-2 text-green-800 dark:text-green-200">
                  <CheckCircle2 className="h-4 w-4" />
                  <span className="text-sm font-medium">Excellent Quality!</span>
                </div>
              </div>
            )}
          </div>
        )}

        <Button
          onClick={handleScore}
          disabled={processing || !imagePath}
          className="w-full"
        >
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            'Score Image Quality'
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
