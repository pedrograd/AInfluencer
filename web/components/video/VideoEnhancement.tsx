'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, Video, CheckCircle2 } from 'lucide-react'

export function VideoEnhancement() {
  const [videoPath, setVideoPath] = useState('')
  const [frameInterpolation, setFrameInterpolation] = useState(false)
  const [targetFps, setTargetFps] = useState(60)
  const [upscale, setUpscale] = useState(false)
  const [targetResolution, setTargetResolution] = useState('4K')
  const [colorGrading, setColorGrading] = useState(false)
  const [gradingPreset, setGradingPreset] = useState('professional')
  const [stabilization, setStabilization] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleEnhance = async () => {
    if (!videoPath) {
      setError('Please provide a video path')
      return
    }

    setProcessing(true)
    setError(null)
    setResult(null)

    try {
      const enhancements: any = {}
      
      if (frameInterpolation) {
        enhancements.frame_interpolation = true
        enhancements.target_fps = targetFps
      }
      
      if (upscale) {
        enhancements.upscale = true
        enhancements.target_resolution = targetResolution
      }
      
      if (colorGrading) {
        enhancements.color_grading = true
        enhancements.preset = gradingPreset
      }
      
      if (stabilization) {
        enhancements.stabilization = true
      }

      const response = await backendAPI.enhanceVideo(videoPath, enhancements)
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const outputPath = data.output_path || data?.output?.path
      const errorMessage = (response as any)?.error?.message

      if (success && outputPath) {
        setResult(outputPath)
      } else {
        setError(errorMessage || 'Video enhancement failed')
      }
    } catch (err: any) {
      setError(err.message || 'Video enhancement failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Video className="h-5 w-5" />
          <span>Video Enhancement</span>
        </CardTitle>
        <CardDescription>
          Enhance videos with frame interpolation, upscaling, color grading, and more
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Video Path</label>
          <Input
            value={videoPath}
            onChange={(e) => setVideoPath(e.target.value)}
            placeholder="/path/to/video.mp4"
          />
        </div>

        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="frame-interpolation"
              checked={frameInterpolation}
              onCheckedChange={(checked) => setFrameInterpolation(checked === true)}
            />
            <label htmlFor="frame-interpolation" className="text-sm font-medium">
              Frame Interpolation
            </label>
          </div>
          {frameInterpolation && (
            <div className="ml-6 space-y-2">
              <label className="text-xs text-muted-foreground">Target FPS</label>
              <Select
                value={targetFps.toString()}
                onValueChange={(value) => setTargetFps(parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="30">30 FPS</SelectItem>
                  <SelectItem value="60">60 FPS</SelectItem>
                  <SelectItem value="120">120 FPS</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="flex items-center space-x-2">
            <Checkbox
              id="upscale"
              checked={upscale}
              onCheckedChange={(checked) => setUpscale(checked === true)}
            />
            <label htmlFor="upscale" className="text-sm font-medium">
              Video Upscaling
            </label>
          </div>
          {upscale && (
            <div className="ml-6 space-y-2">
              <label className="text-xs text-muted-foreground">Target Resolution</label>
              <Select value={targetResolution} onValueChange={setTargetResolution}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1080p">1080p</SelectItem>
                  <SelectItem value="4K">4K</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="flex items-center space-x-2">
            <Checkbox
              id="color-grading"
              checked={colorGrading}
              onCheckedChange={(checked) => setColorGrading(checked === true)}
            />
            <label htmlFor="color-grading" className="text-sm font-medium">
              Color Grading
            </label>
          </div>
          {colorGrading && (
            <div className="ml-6 space-y-2">
              <label className="text-xs text-muted-foreground">Preset</label>
              <Select value={gradingPreset} onValueChange={setGradingPreset}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="instagram">Instagram</SelectItem>
                  <SelectItem value="onlyfans">OnlyFans</SelectItem>
                  <SelectItem value="professional">Professional</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="flex items-center space-x-2">
            <Checkbox
              id="stabilization"
              checked={stabilization}
              onCheckedChange={(checked) => setStabilization(checked === true)}
            />
            <label htmlFor="stabilization" className="text-sm font-medium">
              Video Stabilization
            </label>
          </div>
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
              <span className="text-sm">Video enhancement completed!</span>
            </div>
            <p className="text-xs text-green-700 dark:text-green-300 mt-1">{result}</p>
          </div>
        )}

        <Button
          onClick={handleEnhance}
          disabled={processing || !videoPath}
          className="w-full"
        >
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Enhancing...
            </>
          ) : (
            'Enhance Video'
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
