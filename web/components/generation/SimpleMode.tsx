'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, Sparkles } from 'lucide-react'

export function SimpleMode() {
  const [prompt, setPrompt] = useState('')
  const [characterId, setCharacterId] = useState<string>('')
  const [style, setStyle] = useState('professional')
  const [quality, setQuality] = useState('balanced')
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!prompt) return

    setProcessing(true)
    setResult(null)

    try {
      // Map quality to settings
      const qualitySettings = {
        fast: { steps: 20, cfg_scale: 7.0 },
        balanced: { steps: 30, cfg_scale: 7.5 },
        ultra: { steps: 50, cfg_scale: 8.0 }
      }

      const response = await backendAPI.generateImage({
        prompt: prompt,
        character_id: characterId || undefined,
        settings: {
          ...qualitySettings[quality as keyof typeof qualitySettings],
          sampler: 'euler',
          model: 'realisticVisionV60_v60B1.safetensors'
        }
      })

      if (response.success) {
        setResult(response.data.job_id)
      }
    } catch (err: any) {
      console.error('Generation error:', err)
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Sparkles className="h-5 w-5" />
          <span>Simple Mode</span>
        </CardTitle>
        <CardDescription>
          One-click generation with smart defaults
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">What do you want to generate?</label>
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the image you want to create..."
            rows={3}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Style</label>
            <Select value={style} onValueChange={setStyle}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="professional">Professional</SelectItem>
                <SelectItem value="casual">Casual</SelectItem>
                <SelectItem value="artistic">Artistic</SelectItem>
                <SelectItem value="realistic">Realistic</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Quality</label>
            <Select value={quality} onValueChange={setQuality}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="fast">Fast</SelectItem>
                <SelectItem value="balanced">Balanced</SelectItem>
                <SelectItem value="ultra">Ultra Quality</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {result && (
          <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
            <p className="text-sm text-green-800 dark:text-green-200">
              Generation started! Job ID: {result}
            </p>
          </div>
        )}

        <Button
          onClick={handleGenerate}
          disabled={processing || !prompt}
          className="w-full"
          size="lg"
        >
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            'Generate Image'
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
