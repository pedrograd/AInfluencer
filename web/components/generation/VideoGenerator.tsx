'use client'

import { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FaceReferenceUpload } from './FaceReferenceUpload'
import { GenerationProgress } from './GenerationProgress'
import { Video, Sparkles, Upload, Play, Download } from 'lucide-react'
import { PromptBuilder } from '@/components/prompts/PromptBuilder'
import type { GenerationProgress as GenerationProgressType } from '@/types/generation'

interface VideoGenerationParams {
  prompt: string
  negativePrompt?: string
  method: string
  imageId?: string
  characterId?: string
  settings: {
    frameCount?: number
    fps?: number
    motionBucket?: number
    width?: number
    height?: number
    steps?: number
    cfgScale?: number
    seed?: number
    duration?: number
  }
  faceConsistency?: {
    enabled: boolean
    method?: string
    strength?: number
  }
  postProcessing?: {
    frameInterpolation?: boolean
    interpolationScale?: number
    upscale?: boolean
    faceRestoration?: boolean
  }
  platform?: string
}

export function VideoGenerator() {
  const [prompt, setPrompt] = useState('')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [method, setMethod] = useState('animatediff')
  const [imageId, setImageId] = useState<string | undefined>()
  const [characterId, setCharacterId] = useState<string | undefined>()
  const [faceReference, setFaceReference] = useState<string | null>(null)
  const [faceStrength, setFaceStrength] = useState([0.8])
  const [faceConsistencyEnabled, setFaceConsistencyEnabled] = useState(true)
  const [faceConsistencyMethod, setFaceConsistencyMethod] = useState('ip_adapter')
  
  // Video settings
  const [frameCount, setFrameCount] = useState([16])
  const [fps, setFps] = useState([8])
  const [motionBucket, setMotionBucket] = useState([127])
  const [width, setWidth] = useState(512)
  const [height, setHeight] = useState(512)
  const [steps, setSteps] = useState([30])
  const [cfgScale, setCfgScale] = useState([7])
  const [seed, setSeed] = useState<number | undefined>()
  const [duration, setDuration] = useState(5)
  
  // Post-processing
  const [frameInterpolation, setFrameInterpolation] = useState(true)
  const [interpolationScale, setInterpolationScale] = useState([2])
  const [upscale, setUpscale] = useState(false)
  const [faceRestoration, setFaceRestoration] = useState(true)
  
  // Platform optimization (use sentinel to avoid empty string Select value)
  const [platform, setPlatform] = useState<string>('none')
  
  // Generation state
  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState<GenerationProgressType | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = useCallback(async () => {
    if (!prompt.trim()) {
      alert('Please enter a prompt')
      return
    }

    setIsGenerating(true)
    setError(null)
    setProgress({
      promptId: 'pending',
      status: 'queued',
      progress: 0,
    })

    try {
      const params: VideoGenerationParams = {
        prompt,
        negativePrompt: negativePrompt || undefined,
        method,
        imageId,
        characterId,
        settings: {
          frameCount: frameCount[0],
          fps: fps[0],
          motionBucket: motionBucket[0],
          width,
          height,
          steps: steps[0],
          cfgScale: cfgScale[0],
          seed,
          duration
        },
        faceConsistency: faceConsistencyEnabled ? {
          enabled: true,
          method: faceConsistencyMethod,
          strength: faceStrength[0]
        } : undefined,
        postProcessing: {
          frameInterpolation,
          interpolationScale: interpolationScale[0],
          upscale,
          faceRestoration
        },
      platform: platform === 'none' ? undefined : platform
      }

      const response = await fetch('/api/generate/video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error?.message || 'Generation failed')
      }

      const data = await response.json()
      setJobId(data.data.job_id)
      
      // Poll for status
      pollJobStatus(data.data.job_id)
      
    } catch (err: any) {
      setError(err.message)
      setIsGenerating(false)
    }
  }, [
    prompt, negativePrompt, method, imageId, characterId, faceReference,
    frameCount, fps, motionBucket, width, height, steps, cfgScale, seed, duration,
    faceConsistencyEnabled, faceConsistencyMethod, faceStrength,
    frameInterpolation, interpolationScale, upscale, faceRestoration, platform
  ])

  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/generate/video/${jobId}`)
        const data = await response.json()
        
        if (data.data.status === 'completed') {
          clearInterval(interval)
          setIsGenerating(false)
          setProgress({
            promptId: jobId,
            status: 'completed',
            progress: 100,
            preview: data.data.preview,
          })
          setResult(data.data)
        } else if (data.data.status === 'failed') {
          clearInterval(interval)
          setIsGenerating(false)
          setError(data.data.error || 'Generation failed')
        } else {
          setProgress({
            promptId: jobId,
            status: data.data.status || 'running',
            progress: (data.data.progress || 0) * 100,
            currentStep: data.data.current_step,
            totalSteps: data.data.total_steps,
            preview: data.data.preview,
            error: data.data.error,
          })
        }
      } catch (err) {
        clearInterval(interval)
        setIsGenerating(false)
        setError('Failed to check status')
      }
    }, 2000)
  }

  const handleRandomSeed = () => {
    setSeed(Math.floor(Math.random() * 1000000))
  }

  const methodInfo = {
    animatediff: { name: 'AnimateDiff', quality: '8.5/10', speed: 'Very Fast', frames: '16' },
    svd: { name: 'Stable Video Diffusion', quality: '9/10', speed: 'Fast', frames: '14-25' },
    modelscope: { name: 'ModelScope', quality: '8/10', speed: 'Medium', frames: 'Variable' },
    veo: { name: 'Google Veo', quality: '9.5/10', speed: 'Medium', frames: 'Variable' },
    luma: { name: 'Luma', quality: '9/10', speed: 'Fast', frames: 'Variable' },
    kling: { name: 'Kling AI', quality: '9/10', speed: 'Medium', frames: 'Variable' }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Left Panel - Controls */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Video Generation Method</CardTitle>
            <CardDescription>Choose the method for video generation</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select value={method} onValueChange={setMethod}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="animatediff">AnimateDiff (Fast, 16 frames)</SelectItem>
                <SelectItem value="svd">Stable Video Diffusion (High Quality, 14-25 frames)</SelectItem>
                <SelectItem value="modelscope">ModelScope (Text-to-Video)</SelectItem>
                <SelectItem value="veo">Google Veo (High Quality)</SelectItem>
                <SelectItem value="luma">Luma (Image-to-Video)</SelectItem>
                <SelectItem value="kling">Kling AI (High Quality)</SelectItem>
              </SelectContent>
            </Select>
            {methodInfo[method as keyof typeof methodInfo] && (
              <div className="p-3 bg-muted rounded-lg text-sm">
                <div className="font-medium">{methodInfo[method as keyof typeof methodInfo].name}</div>
                <div className="text-muted-foreground mt-1">
                  Quality: {methodInfo[method as keyof typeof methodInfo].quality} | 
                  Speed: {methodInfo[method as keyof typeof methodInfo].speed} | 
                  Frames: {methodInfo[method as keyof typeof methodInfo].frames}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Generate Prompt</CardTitle>
            <CardDescription>Build an optimized prompt and send it here</CardDescription>
          </CardHeader>
          <CardContent>
            <PromptBuilder
              onPromptGenerated={(p, n) => {
                if (p) setPrompt(p)
                if (typeof n === 'string') setNegativePrompt(n)
              }}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Prompt</CardTitle>
            <CardDescription>Describe the video you want to generate</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="A beautiful woman walking in a park, smooth motion, natural movement, professional video, highly detailed..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="min-h-[120px]"
            />
            <div>
              <label className="text-sm font-medium mb-2 block">Negative Prompt</label>
              <Textarea
                placeholder="blurry, low quality, distorted, flickering, artifacts..."
                value={negativePrompt}
                onChange={(e) => setNegativePrompt(e.target.value)}
                className="min-h-[80px]"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Face Reference</CardTitle>
            <CardDescription>Maintain consistent face across video frames</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="face-consistency"
                checked={faceConsistencyEnabled}
                onChange={(e) => setFaceConsistencyEnabled(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="face-consistency" className="text-sm font-medium">
                Enable Face Consistency
              </label>
            </div>
            {faceConsistencyEnabled && (
              <>
                <FaceReferenceUpload
                  value={faceReference}
                  onChange={setFaceReference}
                  faceStrength={faceStrength[0]}
                  onFaceStrengthChange={(value) => setFaceStrength([value])}
                />
                <Select value={faceConsistencyMethod} onValueChange={setFaceConsistencyMethod}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ip_adapter">IP-Adapter (Fast, 8.5/10)</SelectItem>
                    <SelectItem value="instantid">InstantID (Best, 9.5/10)</SelectItem>
                    <SelectItem value="faceid">FaceID (Good, 9/10)</SelectItem>
                    <SelectItem value="lora">LoRA (Perfect, 10/10)</SelectItem>
                  </SelectContent>
                </Select>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Video Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Frame Count: {frameCount[0]}
              </label>
              <Slider
                value={frameCount}
                onValueChange={setFrameCount}
                min={8}
                max={25}
                step={1}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                FPS: {fps[0]}
              </label>
              <Slider
                value={fps}
                onValueChange={setFps}
                min={8}
                max={30}
                step={1}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                Motion Bucket: {motionBucket[0]}
              </label>
              <Slider
                value={motionBucket}
                onValueChange={setMotionBucket}
                min={1}
                max={255}
                step={1}
              />
              <p className="text-xs text-muted-foreground mt-1">
                127 = balanced, higher = more motion
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Width</label>
                <Input
                  type="number"
                  value={width}
                  onChange={(e) => setWidth(parseInt(e.target.value))}
                  min={256}
                  max={1920}
                  step={64}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Height</label>
                <Input
                  type="number"
                  value={height}
                  onChange={(e) => setHeight(parseInt(e.target.value))}
                  min={256}
                  max={1920}
                  step={64}
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                Steps: {steps[0]}
              </label>
              <Slider
                value={steps}
                onValueChange={setSteps}
                min={20}
                max={50}
                step={1}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                CFG Scale: {cfgScale[0]}
              </label>
              <Slider
                value={cfgScale}
                onValueChange={setCfgScale}
                min={1}
                max={15}
                step={0.5}
              />
            </div>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                placeholder="Seed (optional)"
                value={seed || ''}
                onChange={(e) => setSeed(e.target.value ? parseInt(e.target.value) : undefined)}
                className="flex-1"
              />
              <Button variant="outline" onClick={handleRandomSeed} size="sm">
                Random
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Post-Processing</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="frame-interpolation"
                checked={frameInterpolation}
                onChange={(e) => setFrameInterpolation(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="frame-interpolation" className="text-sm font-medium">
                Frame Interpolation (Smoother motion)
              </label>
            </div>
            {frameInterpolation && (
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Interpolation Scale: {interpolationScale[0]}x
                </label>
                <Slider
                  value={interpolationScale}
                  onValueChange={setInterpolationScale}
                  min={2}
                  max={4}
                  step={1}
                />
              </div>
            )}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="upscale"
                checked={upscale}
                onChange={(e) => setUpscale(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="upscale" className="text-sm font-medium">
                Upscale Video
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="face-restoration"
                checked={faceRestoration}
                onChange={(e) => setFaceRestoration(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="face-restoration" className="text-sm font-medium">
                Face Restoration
              </label>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Platform Optimization</CardTitle>
            <CardDescription>Optimize for specific platform</CardDescription>
          </CardHeader>
          <CardContent>
            <Select value={platform} onValueChange={setPlatform}>
              <SelectTrigger>
                <SelectValue placeholder="Select platform (optional)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="instagram_reels">Instagram Reels (1080x1920, 30fps)</SelectItem>
                <SelectItem value="onlyfans">OnlyFans (1080x1920, 24fps)</SelectItem>
                <SelectItem value="youtube">YouTube (1920x1080, 24fps)</SelectItem>
                <SelectItem value="youtube_shorts">YouTube Shorts (1080x1920, 30fps)</SelectItem>
                <SelectItem value="twitter">Twitter (1280x720, 30fps)</SelectItem>
                <SelectItem value="tiktok">TikTok (1080x1920, 30fps)</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Button
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim()}
          className="w-full"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Sparkles className="mr-2 h-4 w-4 animate-spin" />
              Generating Video...
            </>
          ) : (
            <>
              <Video className="mr-2 h-4 w-4" />
              Generate Video
            </>
          )}
        </Button>

        {error && (
          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="text-destructive">Generation Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Right Panel - Preview & Results */}
      <div className="space-y-6">
        {isGenerating && (
          <Card>
            <CardHeader>
              <CardTitle>Generation Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <GenerationProgress progress={progress} />
              <p className="text-sm text-muted-foreground mt-2">
                Method: {methodInfo[method as keyof typeof methodInfo]?.name || method}
              </p>
            </CardContent>
          </Card>
        )}

        {result && (
          <Card>
            <CardHeader>
              <CardTitle>Generated Video</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {result.media_id && (
                <div className="space-y-2">
                  <video
                    src={`/api/media/${result.media_id}/download`}
                    controls
                    className="w-full rounded-lg"
                  />
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      Job ID: {result.job_id}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        window.open(`/api/media/${result.media_id}/download`, '_blank')
                      }}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Download
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {!isGenerating && !result && (
          <Card>
            <CardContent className="flex items-center justify-center min-h-[400px]">
              <div className="text-center text-muted-foreground">
                <Video className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Generated video will appear here</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
