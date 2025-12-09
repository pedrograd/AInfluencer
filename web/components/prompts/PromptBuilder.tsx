'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Sparkles, Wand2, Copy, Check } from 'lucide-react'
import { promptsAPI } from '@/lib/api/prompts'

interface PromptBuilderProps {
  onPromptGenerated?: (prompt: string, negativePrompt: string) => void
  characterId?: string
}

type PlatformOption = '' | 'instagram' | 'onlyfans' | 'twitter' | 'youtube'

export function PromptBuilder({ onPromptGenerated, characterId }: PromptBuilderProps) {
  const [characterDescription, setCharacterDescription] = useState('')
  const [pose, setPose] = useState('')
  const [setting, setSetting] = useState('')
  const [style, setStyle] = useState('')
  const [platform, setPlatform] = useState<PlatformOption>('')
  const [generatedPrompt, setGeneratedPrompt] = useState('')
  const [generatedNegative, setGeneratedNegative] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleBuildPrompt = async () => {
    setIsGenerating(true)
    try {
      const response = await promptsAPI.build({
        character_description: characterDescription || undefined,
        pose: pose || undefined,
        setting: setting || undefined,
        style: style || undefined,
        platform: platform || undefined,
      })

      if (response.success) {
        const prompt = response.data.prompt || response.data.data?.prompt
        const negative = response.data.negative_prompt || response.data.data?.negative_prompt
        setGeneratedPrompt(prompt)
        setGeneratedNegative(negative)
        if (onPromptGenerated) {
          onPromptGenerated(prompt, negative)
        }
      } else {
        console.error('Build prompt failed:', response)
        alert('Failed to build prompt: ' + (response.error || response.message || 'Unknown error'))
      }
    } catch (error: any) {
      console.error('Error building prompt:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error'
      alert('Failed to build prompt: ' + errorMessage)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleOptimize = async () => {
    if (!generatedPrompt) {
      alert('Please build a prompt first')
      return
    }

    setIsGenerating(true)
    try {
      const response = await promptsAPI.optimize({
        prompt: generatedPrompt,
        target_quality: 'high',
      })

      if (response.success) {
        const optimized = response.data.optimized || response.data.data?.optimized
        setGeneratedPrompt(optimized)
        if (onPromptGenerated) {
          onPromptGenerated(optimized, generatedNegative)
        }
      }
    } catch (error) {
      console.error('Error optimizing prompt:', error)
      alert('Failed to optimize prompt. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wand2 className="h-5 w-5" />
          Advanced Prompt Builder
        </CardTitle>
        <CardDescription>
          Build optimized prompts from components
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs defaultValue="components">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="components">Components</TabsTrigger>
            <TabsTrigger value="result">Result</TabsTrigger>
          </TabsList>

          <TabsContent value="components" className="space-y-4">
            <div className="space-y-2">
              <Label>Character Description</Label>
              <Textarea
                placeholder="A 25-year-old woman, athletic build, long dark hair..."
                value={characterDescription}
                onChange={(e) => setCharacterDescription(e.target.value)}
                className="min-h-[80px]"
              />
            </div>

            <div className="space-y-2">
              <Label>Pose/Action</Label>
              <Input
                placeholder="standing pose, natural smile, looking at camera"
                value={pose}
                onChange={(e) => setPose(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Setting/Environment</Label>
              <Input
                placeholder="modern coffee shop, soft natural lighting"
                value={setting}
                onChange={(e) => setSetting(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Style</Label>
              <Input
                placeholder="professional photography, fashion photography aesthetic"
                value={style}
                onChange={(e) => setStyle(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Platform</Label>
              <Select value={platform} onValueChange={(value) => setPlatform(value as PlatformOption)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select platform" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="instagram">Instagram</SelectItem>
                  <SelectItem value="onlyfans">OnlyFans</SelectItem>
                  <SelectItem value="twitter">Twitter/X</SelectItem>
                  <SelectItem value="youtube">YouTube</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleBuildPrompt}
              disabled={isGenerating}
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <Sparkles className="mr-2 h-4 w-4 animate-spin" />
                  Building...
                </>
              ) : (
                <>
                  <Wand2 className="mr-2 h-4 w-4" />
                  Build Prompt
                </>
              )}
            </Button>
          </TabsContent>

          <TabsContent value="result" className="space-y-4">
            {generatedPrompt ? (
              <>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Generated Prompt</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(generatedPrompt)}
                    >
                      {copied ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  <Textarea
                    value={generatedPrompt}
                    readOnly
                    className="min-h-[120px] font-mono text-sm"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Negative Prompt</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(generatedNegative)}
                    >
                      {copied ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  <Textarea
                    value={generatedNegative}
                    readOnly
                    className="min-h-[100px] font-mono text-sm"
                  />
                </div>

                <Button
                  onClick={handleOptimize}
                  disabled={isGenerating}
                  variant="outline"
                  className="w-full"
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  Optimize Prompt
                </Button>
              </>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <Wand2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Build a prompt using the Components tab</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
