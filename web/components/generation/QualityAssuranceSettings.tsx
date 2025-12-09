'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { CheckCircle2, XCircle } from 'lucide-react'

export interface QualityAssuranceConfig {
  enabled: boolean
  min_score: number
  auto_reject: boolean
  show_scores: boolean
}

interface QualityAssuranceSettingsProps {
  config: QualityAssuranceConfig
  onChange: (config: QualityAssuranceConfig) => void
  qualityScores?: {
    overall: number
    face: number
    technical: number
    realism: number
    artifacts: number
  }
}

export function QualityAssuranceSettings({ 
  config, 
  onChange,
  qualityScores 
}: QualityAssuranceSettingsProps) {
  const updateConfig = (updates: Partial<QualityAssuranceConfig>) => {
    onChange({ ...config, ...updates })
  }

  const getScoreColor = (score: number) => {
    if (score >= 9.0) return 'text-green-600'
    if (score >= 8.0) return 'text-blue-600'
    if (score >= 7.0) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 8.0) {
      return <CheckCircle2 className="h-4 w-4 text-green-600" />
    }
    return <XCircle className="h-4 w-4 text-red-600" />
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quality Assurance</CardTitle>
        <CardDescription>
          Automatic quality scoring and validation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="qa-enabled">Enable Quality Check</Label>
          <Switch
            id="qa-enabled"
            checked={config.enabled}
            onCheckedChange={(checked) => updateConfig({ enabled: checked })}
          />
        </div>

        {config.enabled && (
          <>
            <div className="space-y-2">
              <Label>Minimum Quality Score: {config.min_score.toFixed(1)}/10</Label>
              <Slider
                value={[config.min_score]}
                onValueChange={([value]) => updateConfig({ min_score: value })}
                min={5.0}
                max={10.0}
                step={0.5}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>5.0 (Low)</span>
                <span>7.5 (Good)</span>
                <span>10.0 (Perfect)</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="auto-reject">Auto-Reject Below Minimum</Label>
              <Switch
                id="auto-reject"
                checked={config.auto_reject}
                onCheckedChange={(checked) => updateConfig({ auto_reject: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="show-scores">Show Quality Scores</Label>
              <Switch
                id="show-scores"
                checked={config.show_scores}
                onCheckedChange={(checked) => updateConfig({ show_scores: checked })}
              />
            </div>

            {qualityScores && config.show_scores && (
              <div className="mt-4 p-4 bg-muted rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="font-semibold">Overall Score</Label>
                  <div className="flex items-center gap-2">
                    {getScoreIcon(qualityScores.overall)}
                    <span className={`font-bold ${getScoreColor(qualityScores.overall)}`}>
                      {qualityScores.overall.toFixed(1)}/10
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Face:</span>{' '}
                    <span className={getScoreColor(qualityScores.face)}>
                      {qualityScores.face.toFixed(1)}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Technical:</span>{' '}
                    <span className={getScoreColor(qualityScores.technical)}>
                      {qualityScores.technical.toFixed(1)}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Realism:</span>{' '}
                    <span className={getScoreColor(qualityScores.realism)}>
                      {qualityScores.realism.toFixed(1)}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Artifacts:</span>{' '}
                    <span className={getScoreColor(10 - qualityScores.artifacts * 10)}>
                      {(10 - qualityScores.artifacts * 10).toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
