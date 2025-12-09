'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export interface PostProcessingConfig {
  enabled: boolean
  upscale: boolean
  upscale_factor: number
  face_restoration: boolean
  color_correction: boolean
  noise_reduction: boolean
  remove_metadata: boolean
  quality_optimization: boolean
  output_format: 'PNG' | 'JPG' | 'WEBP'
  quality: number
}

interface PostProcessingSettingsProps {
  config: PostProcessingConfig
  onChange: (config: PostProcessingConfig) => void
}

export function PostProcessingSettings({ config, onChange }: PostProcessingSettingsProps) {
  const updateConfig = (updates: Partial<PostProcessingConfig>) => {
    onChange({ ...config, ...updates })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Post-Processing</CardTitle>
        <CardDescription>
          Enhance and optimize generated images
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="post-processing-enabled">Enable Post-Processing</Label>
          <Switch
            id="post-processing-enabled"
            checked={config.enabled}
            onCheckedChange={(checked) => updateConfig({ enabled: checked })}
          />
        </div>

        {config.enabled && (
          <>
            <div className="flex items-center justify-between">
              <Label htmlFor="upscale">Upscaling</Label>
              <Switch
                id="upscale"
                checked={config.upscale}
                onCheckedChange={(checked) => updateConfig({ upscale: checked })}
              />
            </div>

            {config.upscale && (
              <div className="space-y-2">
                <Label>Upscale Factor: {config.upscale_factor}x</Label>
                <Slider
                  value={[config.upscale_factor]}
                  onValueChange={([value]) => updateConfig({ upscale_factor: value })}
                  min={2}
                  max={8}
                  step={1}
                />
              </div>
            )}

            <div className="flex items-center justify-between">
              <Label htmlFor="face-restoration">Face Restoration</Label>
              <Switch
                id="face-restoration"
                checked={config.face_restoration}
                onCheckedChange={(checked) => updateConfig({ face_restoration: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="color-correction">Color Correction</Label>
              <Switch
                id="color-correction"
                checked={config.color_correction}
                onCheckedChange={(checked) => updateConfig({ color_correction: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="noise-reduction">Noise Reduction</Label>
              <Switch
                id="noise-reduction"
                checked={config.noise_reduction}
                onCheckedChange={(checked) => updateConfig({ noise_reduction: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="remove-metadata" className="text-destructive">
                Remove Metadata (Critical for Anti-Detection)
              </Label>
              <Switch
                id="remove-metadata"
                checked={config.remove_metadata}
                onCheckedChange={(checked) => updateConfig({ remove_metadata: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="quality-optimization">Quality Optimization</Label>
              <Switch
                id="quality-optimization"
                checked={config.quality_optimization}
                onCheckedChange={(checked) => updateConfig({ quality_optimization: checked })}
              />
            </div>

            <div className="space-y-2">
              <Label>Output Format</Label>
              <Select
                value={config.output_format}
                onValueChange={(value) => updateConfig({ output_format: value as 'PNG' | 'JPG' | 'WEBP' })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PNG">PNG (Lossless)</SelectItem>
                  <SelectItem value="JPG">JPG (Compressed)</SelectItem>
                  <SelectItem value="WEBP">WebP (Modern)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {config.output_format !== 'PNG' && (
              <div className="space-y-2">
                <Label>Quality: {config.quality}%</Label>
                <Slider
                  value={[config.quality]}
                  onValueChange={([value]) => updateConfig({ quality: value })}
                  min={50}
                  max={100}
                  step={5}
                />
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
