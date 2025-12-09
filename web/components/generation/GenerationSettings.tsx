'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Settings2, Shuffle } from 'lucide-react'
import { useState } from 'react'

interface GenerationSettingsProps {
  cfg: number
  onCfgChange: (value: number) => void
  steps: number
  onStepsChange: (value: number) => void
  seed?: number
  onSeedChange: (value: number | undefined) => void
  width: number
  onWidthChange: (value: number) => void
  height: number
  onHeightChange: (value: number) => void
  sampler: string
  onSamplerChange: (value: string) => void
  qualityPreset: 'fast' | 'balanced' | 'ultra'
  onQualityPresetChange: (value: 'fast' | 'balanced' | 'ultra') => void
  batchCount: number
  onBatchCountChange: (value: number) => void
  onRandomSeed: () => void
}

export function GenerationSettings({
  cfg,
  onCfgChange,
  steps,
  onStepsChange,
  seed,
  onSeedChange,
  width,
  onWidthChange,
  height,
  onHeightChange,
  sampler,
  onSamplerChange,
  qualityPreset,
  onQualityPresetChange,
  batchCount,
  onBatchCountChange,
  onRandomSeed,
}: GenerationSettingsProps) {
  const [isOpen, setIsOpen] = useState(false)

  const aspectRatios = [
    { label: 'Square (1:1)', width: 1024, height: 1024 },
    { label: 'Portrait (2:3)', width: 832, height: 1216 },
    { label: 'Landscape (3:2)', width: 1216, height: 832 },
    { label: 'Wide (16:9)', width: 1344, height: 768 },
    { label: 'Tall (9:16)', width: 768, height: 1344 },
  ]

  const handleAspectRatio = (ratio: typeof aspectRatios[0]) => {
    onWidthChange(ratio.width)
    onHeightChange(ratio.height)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Settings2 className="h-5 w-5" />
              <span>Advanced Settings</span>
            </CardTitle>
            <CardDescription>Fine-tune generation parameters</CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? 'Collapse' : 'Expand'}
          </Button>
        </div>
      </CardHeader>
      {isOpen && (
        <CardContent className="space-y-6">
          {/* Quality Preset */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Quality Preset</label>
            <Select value={qualityPreset} onValueChange={onQualityPresetChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="fast">Fast (20 steps, lower quality)</SelectItem>
                <SelectItem value="balanced">Balanced (30 steps, good quality)</SelectItem>
                <SelectItem value="ultra">Ultra (50 steps, highest quality)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* CFG Scale */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">CFG Scale</label>
              <span className="text-sm text-muted-foreground">{cfg}</span>
            </div>
            <Slider
              value={[cfg]}
              onValueChange={(values) => onCfgChange(values[0])}
              min={1}
              max={20}
              step={0.5}
            />
            <p className="text-xs text-muted-foreground">
              How closely to follow the prompt (1-20)
            </p>
          </div>

          {/* Steps */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Steps</label>
              <span className="text-sm text-muted-foreground">{steps}</span>
            </div>
            <Slider
              value={[steps]}
              onValueChange={(values) => onStepsChange(values[0])}
              min={20}
              max={100}
              step={1}
            />
            <p className="text-xs text-muted-foreground">
              Number of denoising steps (more = better quality, slower)
            </p>
          </div>

          {/* Sampler */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Sampler</label>
            <Select value={sampler} onValueChange={onSamplerChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="euler">Euler</SelectItem>
                <SelectItem value="euler_ancestral">Euler Ancestral</SelectItem>
                <SelectItem value="dpm_2">DPM++ 2M</SelectItem>
                <SelectItem value="dpm_2_ancestral">DPM++ 2M Karras</SelectItem>
                <SelectItem value="lms">LMS</SelectItem>
                <SelectItem value="ddim">DDIM</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Seed */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Seed</label>
              <Button
                variant="ghost"
                size="sm"
                onClick={onRandomSeed}
              >
                <Shuffle className="mr-2 h-4 w-4" />
                Random
              </Button>
            </div>
            <Input
              type="number"
              value={seed ?? ''}
              onChange={(e) => {
                const value = e.target.value
                onSeedChange(value ? parseInt(value, 10) : undefined)
              }}
              placeholder="Random"
            />
            <p className="text-xs text-muted-foreground">
              Use the same seed to reproduce results
            </p>
          </div>

          {/* Aspect Ratio */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Aspect Ratio</label>
            <div className="grid grid-cols-2 gap-2">
              {aspectRatios.map((ratio) => (
                <Button
                  key={ratio.label}
                  variant={width === ratio.width && height === ratio.height ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleAspectRatio(ratio)}
                >
                  {ratio.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Custom Resolution */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Width</label>
              <Input
                type="number"
                value={width}
                onChange={(e) => onWidthChange(parseInt(e.target.value, 10))}
                min={512}
                max={2048}
                step={64}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Height</label>
              <Input
                type="number"
                value={height}
                onChange={(e) => onHeightChange(parseInt(e.target.value, 10))}
                min={512}
                max={2048}
                step={64}
              />
            </div>
          </div>

          {/* Batch Count */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Batch Count</label>
              <span className="text-sm text-muted-foreground">{batchCount}</span>
            </div>
            <Slider
              value={[batchCount]}
              onValueChange={(values) => onBatchCountChange(values[0])}
              min={1}
              max={10}
              step={1}
            />
            <p className="text-xs text-muted-foreground">
              Number of images to generate
            </p>
          </div>
        </CardContent>
      )}
    </Card>
  )
}
