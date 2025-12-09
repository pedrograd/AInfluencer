'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, Move, Upload } from 'lucide-react'

export function ControlNetTool() {
  const [controlType, setControlType] = useState<'pose' | 'depth' | 'edges'>('pose')
  const [prompt, setPrompt] = useState('')
  const [controlImagePath, setControlImagePath] = useState('')
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!prompt || !controlImagePath) {
      setError('Please provide prompt and control image path')
      return
    }

    setProcessing(true)
    setError(null)
    setResult(null)

    try {
      const handler =
        controlType === 'pose'
          ? backendAPI.generateWithPose
          : controlType === 'depth'
            ? backendAPI.generateWithDepth
            : backendAPI.generateWithEdges

      const response = await handler(prompt, controlImagePath, {})
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const errorMessage = (response as any)?.error?.message

      if (success) {
        setResult(data.output_path || data?.output?.path || JSON.stringify(data))
      } else {
        setError(errorMessage || 'ControlNet generation failed')
      }
    } catch (err: any) {
      setError(err.message || 'ControlNet generation failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Move className="h-5 w-5" />
          <span>ControlNet Generation</span>
        </CardTitle>
        <CardDescription>
          Generate images with precise control using pose, depth, or edge maps
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Control Type</label>
          <Select
            value={controlType}
            onValueChange={(value: 'pose' | 'depth' | 'edges') => setControlType(value)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pose">Pose Control</SelectItem>
              <SelectItem value="depth">Depth Control</SelectItem>
              <SelectItem value="edges">Edge Control (Canny)</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            {controlType === 'pose' && 'Control character poses and body positions'}
            {controlType === 'depth' && 'Control scene depth and composition'}
            {controlType === 'edges' && 'Control edges and structure'}
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Control Image Path</label>
          <Input
            value={controlImagePath}
            onChange={(e) => setControlImagePath(e.target.value)}
            placeholder="/path/to/control-image.png"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Prompt</label>
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the image you want to generate..."
            rows={3}
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-sm text-red-800 dark:text-red-200">
            {error}
          </div>
        )}

        {result && (
          <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
            <p className="text-sm text-green-800 dark:text-green-200">Result: {result}</p>
          </div>
        )}

        <Button
          onClick={handleGenerate}
          disabled={processing || !prompt || !controlImagePath}
          className="w-full"
        >
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Generate with ControlNet
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
