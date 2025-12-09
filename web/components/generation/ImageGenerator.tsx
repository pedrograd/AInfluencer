'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { FaceConsistencySettings } from './FaceConsistencySettings'
import { GenerationSettings } from './GenerationSettings'
import { GenerationProgress } from './GenerationProgress'
import { PromptBuilder } from '@/components/prompts/PromptBuilder'
import { PostProcessingSettings, type PostProcessingConfig } from './PostProcessingSettings'
import { AntiDetectionSettings, type AntiDetectionConfig } from './AntiDetectionSettings'
import { QualityAssuranceSettings, type QualityAssuranceConfig } from './QualityAssuranceSettings'
import { useImageGeneration } from '@/hooks/useGeneration'
import { Download, Sparkles } from 'lucide-react'
import type { FaceConsistencyConfig } from '@/types/generation'
import { getFeatureFlags } from '@/lib/features'

export function ImageGenerator() {
  const flags = useMemo(() => getFeatureFlags(), [])
  const [prompt, setPrompt] = useState('')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [characterId, setCharacterId] = useState<string | undefined>()
  const [cfg, setCfg] = useState([7])
  const [steps, setSteps] = useState([30])
  const [seed, setSeed] = useState<number | undefined>()
  const [width, setWidth] = useState(1024)
  const [height, setHeight] = useState(1024)
  const [sampler, setSampler] = useState('euler')
  const [qualityPreset, setQualityPreset] = useState<'fast' | 'balanced' | 'ultra'>('balanced')
  const [batchCount, setBatchCount] = useState(1)
  const [faceConsistency, setFaceConsistency] = useState<FaceConsistencyConfig>({
    enabled: false,
    method: 'ip_adapter',
    strength: 0.8,
  })
  const [postProcessing, setPostProcessing] = useState<PostProcessingConfig>({
    enabled: true,
    upscale: true,
    upscale_factor: 4,
    face_restoration: true,
    color_correction: true,
    noise_reduction: false,
    remove_metadata: true,
    quality_optimization: true,
    output_format: 'PNG',
    quality: 95,
  })
  const [antiDetection, setAntiDetection] = useState<AntiDetectionConfig>({
    enabled: true,
    remove_metadata: true,
    add_imperfections: true,
    vary_quality: true,
    remove_ai_signatures: true,
    add_realistic_noise: false,
    normalize_colors: true,
  })
  const [qualityAssurance, setQualityAssurance] = useState<QualityAssuranceConfig>({
    enabled: true,
    min_score: 8.0,
    auto_reject: true,
    show_scores: true,
  })
  const [lowResourceMode, setLowResourceMode] = useState(false)
  const initializedDemoRef = useRef(false)
  const previousSettingsRef = useRef<{
    cfg: number
    steps: number
    width: number
    height: number
    sampler: string
    qualityPreset: 'fast' | 'balanced' | 'ultra'
    batchCount: number
    postProcessing: PostProcessingConfig
    antiDetection: AntiDetectionConfig
  } | null>(null)

  const {
    generate,
    isGenerating,
    progress,
    results,
    error,
    troubleshootingInfo,
  } = useImageGeneration()

  // Enforce feature flag defaults in demo mode
  useEffect(() => {
    if (flags.demoMode && !initializedDemoRef.current) {
      initializedDemoRef.current = true
      handleLowResourceToggle(true)
    }
  }, [flags.demoMode])

  useEffect(() => {
    if (!flags.enableUpscale) {
      setPostProcessing((prev) => ({ ...prev, upscale: false }))
    }
    if (!flags.enableFaceRestore) {
      setPostProcessing((prev) => ({ ...prev, face_restoration: false }))
    }
    if (!flags.enableBatch && batchCount > 1) {
      setBatchCount(1)
    }
    if (!flags.enableHighRes) {
      setWidth((w) => Math.min(w, flags.demoMaxWidth))
      setHeight((h) => Math.min(h, flags.demoMaxHeight))
    }
  }, [flags.enableUpscale, flags.enableFaceRestore, flags.enableBatch, flags.enableHighRes, flags.demoMaxHeight, flags.demoMaxWidth, batchCount])

  const handleGenerate = useCallback(() => {
    if (!prompt.trim()) {
      alert('Please enter a prompt')
      return
    }

    const safeWidth = flags.enableHighRes ? width : Math.min(width, flags.demoMaxWidth)
    const safeHeight = flags.enableHighRes ? height : Math.min(height, flags.demoMaxHeight)
    const safeBatch = flags.enableBatch ? batchCount : 1

    generate({
      prompt,
      negativePrompt: negativePrompt || undefined,
      characterId,
      cfg: cfg[0],
      steps: steps[0],
      seed,
      width: safeWidth,
      height: safeHeight,
      sampler,
      qualityPreset,
      batchCount: safeBatch,
      faceConsistency: faceConsistency.enabled ? faceConsistency : undefined,
      postProcessing:
        postProcessing.enabled && flags.enableUpscale
          ? {
              ...postProcessing,
              face_restoration: flags.enableFaceRestore ? postProcessing.face_restoration : false,
            }
          : { ...postProcessing, upscale: false, face_restoration: false },
      antiDetection: antiDetection.enabled ? antiDetection : undefined,
      qualityCheck: qualityAssurance.enabled
        ? {
            enabled: qualityAssurance.enabled,
            min_score: qualityAssurance.min_score,
          }
        : undefined,
    })
  }, [
    prompt,
    negativePrompt,
    characterId,
    cfg,
    steps,
    seed,
    width,
    height,
    sampler,
    qualityPreset,
    batchCount,
    faceConsistency,
    postProcessing,
    antiDetection,
    qualityAssurance,
    generate,
    flags.enableBatch,
    flags.enableFaceRestore,
    flags.enableHighRes,
    flags.enableUpscale,
    flags.demoMaxHeight,
    flags.demoMaxWidth,
  ])

  const handleRandomSeed = () => {
    setSeed(Math.floor(Math.random() * 1000000))
  }

  const handlePromptGenerated = (newPrompt: string, newNegativePrompt: string) => {
    setPrompt(newPrompt)
    setNegativePrompt(newNegativePrompt)
  }

  const handleLowResourceToggle = (enabled: boolean) => {
    setLowResourceMode(enabled)

    if (enabled) {
      previousSettingsRef.current = {
        cfg: cfg[0],
        steps: steps[0],
        width,
        height,
        sampler,
        qualityPreset,
        batchCount,
        postProcessing: { ...postProcessing },
        antiDetection: { ...antiDetection },
      }

      setSteps([18])
      setCfg([6])
      setWidth(768)
      setHeight(768)
      setSampler('euler')
      setQualityPreset('fast')
      setBatchCount(1)
      setPostProcessing((prev) => ({
        ...prev,
        upscale: false,
        face_restoration: false,
        quality: Math.min(prev.quality, 85),
      }))
      setAntiDetection((prev) => ({
        ...prev,
        vary_quality: false,
      }))
      return
    }

    if (previousSettingsRef.current) {
      const previous = previousSettingsRef.current
      setCfg([previous.cfg])
      setSteps([previous.steps])
      setWidth(previous.width)
      setHeight(previous.height)
      setSampler(previous.sampler)
      setQualityPreset(previous.qualityPreset)
      setBatchCount(previous.batchCount)
      setPostProcessing(previous.postProcessing)
      setAntiDetection(previous.antiDetection)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Left Panel - Controls */}
      <div className="space-y-6">
        {(flags.demoMode || !flags.enableHighRes) && (
          <Alert>
            <AlertTitle>Demo mode / CPU tier active</AlertTitle>
            <AlertDescription>
              Demo limits: low-resolution defaults, batch size capped at {flags.demoMaxBatch}, and heavy
              upscaling/face restoration may be disabled on free tiers.
            </AlertDescription>
          </Alert>
        )}

        <PromptBuilder
          onPromptGenerated={handlePromptGenerated}
          characterId={characterId}
        />

        <Card>
          <CardHeader>
            <CardTitle>Prompt</CardTitle>
            <CardDescription>Describe the image you want to generate (or use Advanced Builder above)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="A beautiful woman, professional photography, high quality, 8k, ultra realistic..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="min-h-[120px]"
            />
            <div>
              <label className="text-sm font-medium mb-2 block">Negative Prompt</label>
              <Textarea
                placeholder="blurry, low quality, distorted, watermark..."
                value={negativePrompt}
                onChange={(e) => setNegativePrompt(e.target.value)}
                className="min-h-[80px]"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Low-resource mode</CardTitle>
            <CardDescription>CPU-friendly preset for free tiers (smaller resolution, fewer steps).</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              <p>768x768, 18 steps, fast sampler, batch size 1, minimal post-processing.</p>
              <p className="mt-1">Recommended for Render free plans or local CPU demos.</p>
            </div>
            <Switch checked={lowResourceMode} onCheckedChange={handleLowResourceToggle} />
          </CardContent>
        </Card>

        <FaceConsistencySettings
          config={faceConsistency}
          onChange={setFaceConsistency}
          characterId={characterId}
        />

        <GenerationSettings
          cfg={cfg[0]}
          onCfgChange={(value) => setCfg([value])}
          steps={steps[0]}
          onStepsChange={(value) => setSteps([value])}
          seed={seed}
          onSeedChange={setSeed}
          width={width}
          onWidthChange={setWidth}
          height={height}
          onHeightChange={setHeight}
          sampler={sampler}
          onSamplerChange={setSampler}
          qualityPreset={qualityPreset}
          onQualityPresetChange={setQualityPreset}
          batchCount={batchCount}
          onBatchCountChange={setBatchCount}
          onRandomSeed={handleRandomSeed}
        />

        <PostProcessingSettings
          config={postProcessing}
          onChange={setPostProcessing}
        />

        <AntiDetectionSettings
          config={antiDetection}
          onChange={setAntiDetection}
        />

        <QualityAssuranceSettings
          config={qualityAssurance}
          onChange={setQualityAssurance}
        />

        <Button
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim()}
          className="w-full"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Sparkles className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Generate Image
            </>
          )}
        </Button>

        {error && (
          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="text-destructive">Generation Error</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-destructive whitespace-pre-wrap">{error}</p>
              
              {troubleshootingInfo && troubleshootingInfo.troubleshooting && (
                <div className="mt-4 p-4 bg-muted rounded-lg border border-primary/20">
                  <h4 className="font-semibold mb-2 text-primary">
                    {troubleshootingInfo.troubleshooting.title || 'Troubleshooting Information'}
                  </h4>
                  {troubleshootingInfo.error_code && (
                    <p className="text-xs text-muted-foreground mb-2">
                      Error Code: <code className="px-1 py-0.5 bg-background rounded">{troubleshootingInfo.error_code}</code>
                    </p>
                  )}
                  {troubleshootingInfo.troubleshooting.solutions && troubleshootingInfo.troubleshooting.solutions.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">Recommended Solutions:</p>
                      <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                        {troubleshootingInfo.troubleshooting.solutions.map((solution, idx) => (
                          <li key={idx}>{solution}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="mt-3 pt-3 border-t">
                    <a
                      href="/#troubleshooting"
                      className="text-sm text-primary hover:underline"
                    >
                      View full troubleshooting guide →
                    </a>
                  </div>
                </div>
              )}
              
              {error.includes('not in') && (
                <div className="mt-4 p-3 bg-muted rounded-lg">
                  <p className="text-xs font-medium mb-2">Tip:</p>
                  <p className="text-xs text-muted-foreground">
                    The model specified in the workflow doesn't match your installed models. 
                    Update the workflow builder in <code className="text-xs">hooks/useGeneration.ts</code> 
                    to use one of your available models.
                  </p>
                </div>
              )}
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
            </CardContent>
          </Card>
        )}

        {results.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Generated Images</CardTitle>
              <CardDescription>{results.length} image(s) generated</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 grid-cols-1">
                {results.map((result, index) => (
                  <div key={result.id} className="space-y-2">
                    <div className="relative aspect-square w-full overflow-hidden rounded-lg border">
                      <img
                        src={result.imageUrl}
                        alt={`Generated image ${index + 1}`}
                        className="h-full w-full object-cover"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-muted-foreground">
                        Seed: {result.metadata.seed}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const link = document.createElement('a')
                          link.href = result.imageUrl
                          link.download = `generated-${result.id}.png`
                          link.click()
                        }}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {!isGenerating && results.length === 0 && (
          <Card>
            <CardContent className="flex items-center justify-center min-h-[400px]">
              <div className="text-center text-muted-foreground">
                <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Generated images will appear here</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
