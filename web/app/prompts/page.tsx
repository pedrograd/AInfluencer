'use client'

import { useState } from 'react'
import { PromptBuilder } from '@/components/prompts/PromptBuilder'
import { PromptSuggestions } from '@/components/generation/PromptSuggestions'
import { PromptTemplates } from '@/components/generation/PromptTemplates'
import { PromptHistory } from '@/components/generation/PromptHistory'
import { VisualPromptBuilder } from '@/components/generation/VisualPromptBuilder'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { ClipboardCheck, Copy } from 'lucide-react'

export default function PromptsPage() {
  const [activePrompt, setActivePrompt] = useState('')
  const [promptSource, setPromptSource] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const handlePromptSelection = (prompt: string, source: string) => {
    if (!prompt) return
    setActivePrompt(prompt)
    setPromptSource(source)
    setCopied(false)
  }

  const handleCopyActive = () => {
    if (!activePrompt) return
    navigator.clipboard.writeText(activePrompt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Advanced Prompt Engineering</h1>
        <p className="text-muted-foreground">
          Build, visualize, and reuse prompts with AI-powered suggestions and history
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <PromptBuilder
            onPromptGenerated={(prompt) => handlePromptSelection(prompt, 'builder')}
          />

          <VisualPromptBuilder
            onPromptGenerated={(prompt) => handlePromptSelection(prompt, 'visual-builder')}
          />

          <PromptSuggestions
            onPromptSelected={(prompt) => handlePromptSelection(prompt, 'suggestion')}
          />
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ClipboardCheck className="h-5 w-5" />
                Selected Prompt
              </CardTitle>
              <CardDescription>
                Capture prompts from builders, suggestions, templates, or history
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                value={activePrompt}
                readOnly
                placeholder="Select or generate a prompt to capture it here"
                className="min-h-[140px] font-mono text-sm"
              />
              <div className="flex items-center justify-between">
                <div className="text-xs text-muted-foreground">
                  {promptSource ? `Source: ${promptSource}` : 'No prompt selected yet'}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyActive}
                  disabled={!activePrompt}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  {copied ? 'Copied' : 'Copy'}
                </Button>
              </div>
            </CardContent>
          </Card>

          <PromptTemplates
            onTemplateSelected={(prompt) => handlePromptSelection(prompt, 'template')}
          />

          <PromptHistory
            onPromptSelected={(prompt) => handlePromptSelection(prompt, 'history')}
          />
        </div>
      </div>
    </div>
  )
}
