'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, Sparkles, Copy, Check } from 'lucide-react'

interface PromptSuggestionsProps {
  onPromptSelected?: (prompt: string) => void
}

export function PromptSuggestions({ onPromptSelected }: PromptSuggestionsProps) {
  const [description, setDescription] = useState('')
  const [style, setStyle] = useState<string>('')
  const [platform, setPlatform] = useState<string>('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  const handleGenerateSuggestions = async () => {
    if (!description.trim()) return

    setLoading(true)
    setSuggestions([])

    try {
      const response = await backendAPI.generatePrompt(description, style || undefined, platform || undefined)
      if (response.success) {
        const allSuggestions = [
          response.data.prompt,
          ...(response.data.suggestions || [])
        ]
        setSuggestions(allSuggestions)
      }
    } catch (err: any) {
      console.error('Prompt generation error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text)
    onPromptSelected?.(text)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Sparkles className="h-5 w-5" />
          <span>AI Prompt Suggestions</span>
        </CardTitle>
        <CardDescription>
          Get AI-powered prompt suggestions based on your description
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Describe what you want</label>
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., A beautiful woman in a professional setting..."
            rows={3}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Style (optional)</label>
            <input
              type="text"
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              placeholder="professional, casual, etc."
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Platform (optional)</label>
            <input
              type="text"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              placeholder="instagram, onlyfans, etc."
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>
        </div>

        <Button
          onClick={handleGenerateSuggestions}
          disabled={loading || !description.trim()}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating Suggestions...
            </>
          ) : (
            'Generate Prompt Suggestions'
          )}
        </Button>

        {suggestions.length > 0 && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Suggested Prompts</label>
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="p-3 bg-secondary rounded-md flex items-start justify-between gap-2"
              >
                <p className="text-sm flex-1">{suggestion}</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleCopy(suggestion, index)}
                >
                  {copiedIndex === index ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
