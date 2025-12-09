'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, Sparkles, CheckCircle2 } from 'lucide-react'

interface HybridFaceRestorationProps {
  imagePath?: string
  onComplete?: (outputPath: string) => void
}

export function HybridFaceRestoration({ imagePath, onComplete }: HybridFaceRestorationProps) {
  const [gfpganWeight, setGfpganWeight] = useState<number>(0.5)
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleRestore = async () => {
    if (!imagePath) {
      setError('Please select an image first')
      return
    }

    setProcessing(true)
    setError(null)
    setResult(null)

    try {
      const response = await backendAPI.hybridFaceRestoration(imagePath, gfpganWeight)
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const outputPath = data.output_path || data?.output?.path
      const errorMessage = (response as any)?.error?.message

      if (success && outputPath) {
        setResult(outputPath)
        onComplete?.(outputPath)
      } else {
        setError(errorMessage || 'Face restoration failed')
      }
    } catch (err: any) {
      setError(err.message || 'Face restoration failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Sparkles className="h-5 w-5" />
          <span>Hybrid Face Restoration</span>
        </CardTitle>
        <CardDescription>
          Combine GFPGAN and CodeFormer for best face restoration quality
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <label className="font-medium">GFPGAN Weight</label>
            <span className="text-muted-foreground">{(gfpganWeight * 100).toFixed(0)}%</span>
          </div>
          <Slider
            value={[gfpganWeight]}
            onValueChange={([value]) => setGfpganWeight(value)}
            min={0}
            max={1}
            step={0.1}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>CodeFormer Only</span>
            <span>GFPGAN Only</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Higher values favor GFPGAN (faster), lower values favor CodeFormer (better quality)
          </p>
        </div>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-sm text-red-800 dark:text-red-200">
            {error}
          </div>
        )}

        {result && (
          <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
            <div className="flex items-center space-x-2 text-green-800 dark:text-green-200">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-sm">Face restoration completed!</span>
            </div>
            <p className="text-xs text-green-700 dark:text-green-300 mt-1">{result}</p>
          </div>
        )}

        <Button
          onClick={handleRestore}
          disabled={processing || !imagePath}
          className="w-full"
        >
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Restoring...
            </>
          ) : (
            'Start Face Restoration'
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
