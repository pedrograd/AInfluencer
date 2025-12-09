'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, Upload, CheckCircle2 } from 'lucide-react'

interface MultiStageUpscaleProps {
  imagePath?: string
  onComplete?: (outputPath: string) => void
}

export function MultiStageUpscale({ imagePath, onComplete }: MultiStageUpscaleProps) {
  const [targetFactor, setTargetFactor] = useState<number>(8)
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleUpscale = async () => {
    if (!imagePath) {
      setError('Please select an image first')
      return
    }

    setProcessing(true)
    setError(null)
    setResult(null)

    try {
      const response = await backendAPI.multiStageUpscale(imagePath, targetFactor)
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const outputPath = data.output_path || data?.output?.path
      const errorMessage = (response as any)?.error?.message

      if (success && outputPath) {
        setResult(outputPath)
        onComplete?.(outputPath)
      } else {
        setError(errorMessage || 'Upscaling failed')
      }
    } catch (err: any) {
      setError(err.message || 'Upscaling failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Multi-Stage Upscaling</CardTitle>
        <CardDescription>
          Upscale images in stages (2x → 4x → 8x) for maximum quality
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Target Upscale Factor</label>
          <Select
            value={targetFactor.toString()}
            onValueChange={(value) => setTargetFactor(parseInt(value))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2">2x (Double)</SelectItem>
              <SelectItem value="4">4x (Quadruple)</SelectItem>
              <SelectItem value="8">8x (Ultra High)</SelectItem>
            </SelectContent>
          </Select>
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
              <span className="text-sm">Upscaling completed!</span>
            </div>
            <p className="text-xs text-green-700 dark:text-green-300 mt-1">{result}</p>
          </div>
        )}

        <Button
          onClick={handleUpscale}
          disabled={processing || !imagePath}
          className="w-full"
        >
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Upscaling...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Start Upscaling
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
