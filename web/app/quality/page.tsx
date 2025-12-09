'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { QualityScoreDisplay } from '@/components/quality/QualityScoreDisplay'
import { qualityAPI } from '@/lib/api/quality'
import { Upload, CheckCircle2 } from 'lucide-react'

export default function QualityPage() {
  const [file, setFile] = useState<File | null>(null)
  const [scores, setScores] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [minScore, setMinScore] = useState(8.0)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setScores(null)
    }
  }

  const handleScore = async () => {
    if (!file) {
      alert('Please select a file')
      return
    }

    setIsLoading(true)
    try {
      // For now, we'll use a placeholder path
      // In production, this would upload the file first
      const response = await qualityAPI.score({
        content_path: `/tmp/${file.name}`,
        content_type: 'image',
      })

      if (response.success) {
        setScores(response.data)
      }
    } catch (error) {
      console.error('Error scoring:', error)
      alert('Failed to score content. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleValidate = async () => {
    if (!file) {
      alert('Please select a file')
      return
    }

    setIsLoading(true)
    try {
      const response = await qualityAPI.validate({
        content_path: `/tmp/${file.name}`,
        content_type: 'image',
        min_score: minScore,
      })

      if (response.success) {
        alert(response.data.passed ? '✅ Content passed quality check!' : '❌ Content failed quality check')
        setScores(response.data.scores)
      }
    } catch (error) {
      console.error('Error validating:', error)
      alert('Failed to validate content. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Quality Assurance</h1>
        <p className="text-muted-foreground">
          Score and validate content quality
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Upload Content</CardTitle>
            <CardDescription>
              Upload an image or video to check quality
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="file">Select File</Label>
              <Input
                id="file"
                type="file"
                accept="image/*,video/*"
                onChange={handleFileChange}
              />
            </div>

            {file && (
              <div className="p-3 bg-muted rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">{file.name}</span>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label>Minimum Score: {minScore.toFixed(1)}/10</Label>
              <input
                type="range"
                min="5"
                max="10"
                step="0.5"
                value={minScore}
                onChange={(e) => setMinScore(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleScore}
                disabled={!file || isLoading}
                className="flex-1"
              >
                <Upload className="mr-2 h-4 w-4" />
                Score Quality
              </Button>
              <Button
                onClick={handleValidate}
                disabled={!file || isLoading}
                variant="outline"
                className="flex-1"
              >
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Validate
              </Button>
            </div>
          </CardContent>
        </Card>

        {scores && (
          <QualityScoreDisplay scores={scores} minScore={minScore} />
        )}
      </div>
    </div>
  )
}
