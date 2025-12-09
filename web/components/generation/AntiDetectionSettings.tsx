'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Shield, AlertTriangle } from 'lucide-react'

export interface AntiDetectionConfig {
  enabled: boolean
  remove_metadata: boolean
  add_imperfections: boolean
  vary_quality: boolean
  remove_ai_signatures: boolean
  add_realistic_noise: boolean
  normalize_colors: boolean
}

interface AntiDetectionSettingsProps {
  config: AntiDetectionConfig
  onChange: (config: AntiDetectionConfig) => void
}

export function AntiDetectionSettings({ config, onChange }: AntiDetectionSettingsProps) {
  const updateConfig = (updates: Partial<AntiDetectionConfig>) => {
    onChange({ ...config, ...updates })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Anti-Detection
        </CardTitle>
        <CardDescription>
          Make content undetectable as AI-generated
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Important</AlertTitle>
          <AlertDescription>
            Anti-detection techniques help make AI-generated content appear more natural and human-like.
            Always enable metadata removal for privacy and security.
          </AlertDescription>
        </Alert>

        <div className="flex items-center justify-between">
          <Label htmlFor="anti-detection-enabled">Enable Anti-Detection</Label>
          <Switch
            id="anti-detection-enabled"
            checked={config.enabled}
            onCheckedChange={(checked) => updateConfig({ enabled: checked })}
          />
        </div>

        {config.enabled && (
          <>
            <div className="flex items-center justify-between">
              <Label htmlFor="remove-metadata" className="text-destructive font-semibold">
                Remove Metadata (Critical)
              </Label>
              <Switch
                id="remove-metadata"
                checked={config.remove_metadata}
                onCheckedChange={(checked) => updateConfig({ remove_metadata: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="add-imperfections">Add Natural Imperfections</Label>
              <Switch
                id="add-imperfections"
                checked={config.add_imperfections}
                onCheckedChange={(checked) => updateConfig({ add_imperfections: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="vary-quality">Vary Quality (Natural Variation)</Label>
              <Switch
                id="vary-quality"
                checked={config.vary_quality}
                onCheckedChange={(checked) => updateConfig({ vary_quality: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="remove-ai-signatures">Remove AI Signatures</Label>
              <Switch
                id="remove-ai-signatures"
                checked={config.remove_ai_signatures}
                onCheckedChange={(checked) => updateConfig({ remove_ai_signatures: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="add-realistic-noise">Add Realistic Noise</Label>
              <Switch
                id="add-realistic-noise"
                checked={config.add_realistic_noise}
                onCheckedChange={(checked) => updateConfig({ add_realistic_noise: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="normalize-colors">Normalize Colors</Label>
              <Switch
                id="normalize-colors"
                checked={config.normalize_colors}
                onCheckedChange={(checked) => updateConfig({ normalize_colors: checked })}
              />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
