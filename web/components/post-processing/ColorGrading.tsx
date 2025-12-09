'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, Palette, CheckCircle2 } from 'lucide-react'

interface ColorGradingProps {
  imagePath?: string
  onComplete?: (outputPath: string) => void
}

export function ColorGrading({ imagePath, onComplete }: ColorGradingProps) {
  const [preset, setPreset] = useState<string>('instagram')
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleGrading = async () => {
    if (!imagePath) {
      setError('Please select an image first')
      return
    }

    setProcessing(true)
    setError(null)
    setResult(null)

    try {
      const response = await backendAPI.colorGrading(imagePath, preset as any)
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const outputPath = data.output_path || data?.output?.path
      const errorMessage = (response as any)?.error?.message

      if (success && outputPath) {
        setResult(outputPath)
        onComplete?.(outputPath)
      } else {
        setError(errorMessage || 'Color grading failed')
      }
    } catch (err: any) {
      setError(err.message || 'Color grading failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Palette className="h-5 w-5" />
          <span>Color Grading Presets</span>
        </CardTitle>
        <CardDescription>
          Apply professional color grading presets optimized for different platforms
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Preset</label>
          <Select value={preset} onValueChange={setPreset}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="instagram">Instagram</SelectItem>
              <SelectItem value="onlyfans">OnlyFans</SelectItem>
              <SelectItem value="professional">Professional</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            {preset === 'instagram' && 'Vibrant colors, high saturation, optimized for social media'}
            {preset === 'onlyfans' && 'Premium look, enhanced colors, professional quality'}
            {preset === 'professional' && 'Natural colors, balanced, professional photography'}
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
              <span className="text-sm">Color grading completed!</span>
            </div>
            <p className="text-xs text-green-700 dark:text-green-300 mt-1">{result}</p>
          </div>
        )}

        <Button
          onClick={handleGrading}
          disabled={processing || !imagePath}
          className="w-full"
        >
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Applying...
            </>
          ) : (
            'Apply Color Grading'
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
