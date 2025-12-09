'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, Paintbrush, Upload } from 'lucide-react'

export function InpaintingTool() {
  const [imagePath, setImagePath] = useState('')
  const [maskPath, setMaskPath] = useState('')
  const [prompt, setPrompt] = useState('')
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleInpaint = async () => {
    if (!imagePath || !maskPath || !prompt) {
      setError('Please provide image path, mask path, and prompt')
      return
    }

    setProcessing(true)
    setError(null)
    setResult(null)

    try {
      const response = await backendAPI.inpaint(imagePath, maskPath, prompt, {})
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const errorMessage = (response as any)?.error?.message

      if (success) {
        setResult(data.output_path || data?.output?.path || JSON.stringify(data))
      } else {
        setError(errorMessage || 'Inpainting failed')
      }
    } catch (err: any) {
      setError(err.message || 'Inpainting failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Paintbrush className="h-5 w-5" />
          <span>Image Inpainting</span>
        </CardTitle>
        <CardDescription>
          Edit specific parts of images by painting over areas to modify
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Image Path</label>
          <Input
            value={imagePath}
            onChange={(e) => setImagePath(e.target.value)}
            placeholder="/path/to/image.png"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Mask Path</label>
          <Input
            value={maskPath}
            onChange={(e) => setMaskPath(e.target.value)}
            placeholder="/path/to/mask.png"
          />
          <p className="text-xs text-muted-foreground">
            White areas in mask = areas to inpaint
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Prompt</label>
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what to paint in the masked area..."
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
          onClick={handleInpaint}
          disabled={processing || !imagePath || !maskPath || !prompt}
          className="w-full"
        >
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Inpainting...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Start Inpainting
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
