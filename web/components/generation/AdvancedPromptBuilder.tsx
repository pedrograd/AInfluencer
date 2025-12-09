'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { backendAPI } from '@/lib/api/backend'
import { Wand2, Sparkles, Copy, Check, RefreshCw } from 'lucide-react'

interface AdvancedPromptBuilderProps {
  onPromptGenerated?: (prompt: string, negativePrompt: string) => void
  characterId?: string
}

export function AdvancedPromptBuilder({ onPromptGenerated, characterId }: AdvancedPromptBuilderProps) {
  const [activeTab, setActiveTab] = useState<'simple' | 'advanced' | 'optimize'>('simple')
  
  // Simple mode
  const [basePrompt, setBasePrompt] = useState('')
  const [variation, setVariation] = useState('default')
  const [platform, setPlatform] = useState<string>('')
  const [generatedPrompt, setGeneratedPrompt] = useState('')
  const [generatedNegative, setGeneratedNegative] = useState('')
  
  // Advanced mode
  const [subject, setSubject] = useState({
    age: '',
    gender: '',
    ethnicity: '',
    build: '',
    height: '',
  })
  const [appearance, setAppearance] = useState({
    eyes: '',
    nose: '',
    lips: '',
    jawline: '',
    cheekbones: '',
    hairColor: '',
    hairLength: '',
    hairStyle: '',
    skinTone: '',
    skinTexture: '',
  })
  const [pose, setPose] = useState({
    position: '',
    expression: '',
    bodyLanguage: '',
    lookingDirection: '',
  })
  const [setting, setSetting] = useState({
    locationType: '',
    specificLocation: '',
    lighting: '',
    timeOfDay: '',
  })
  
  // Optimize mode
  const [promptToOptimize, setPromptToOptimize] = useState('')
  const [optimizedPrompt, setOptimizedPrompt] = useState('')
  
  const [isGenerating, setIsGenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [platforms, setPlatforms] = useState<Record<string, any>>({})
  const [templates, setTemplates] = useState<any>(null)

  useEffect(() => {
    loadPlatforms()
    loadTemplates()
  }, [])

  const loadPlatforms = async () => {
    try {
      const response = await backendAPI.getPlatformStyles()
      if (response.success) {
        setPlatforms(response.data.platforms)
      }
    } catch (error) {
      console.error('Failed to load platforms:', error)
    }
  }

  const loadTemplates = async () => {
    try {
      const response = await backendAPI.getPromptTemplates()
      if (response.success) {
        setTemplates(response.data)
      }
    } catch (error) {
      console.error('Failed to load templates:', error)
    }
  }

  const handleBuildPrompt = async () => {
    setIsGenerating(true)
    try {
      const params: any = {
        variation,
      }
      
      if (characterId) {
        params.character_id = characterId
      }
      
      if (platform) {
        params.platform = platform
      }
      
      if (activeTab === 'simple' && basePrompt) {
        params.base_prompt = basePrompt
      } else if (activeTab === 'advanced') {
        params.subject = {
          age: subject.age ? parseInt(subject.age) : undefined,
          gender: subject.gender || undefined,
          ethnicity: subject.ethnicity || undefined,
          build: subject.build || undefined,
          height: subject.height || undefined,
        }
        params.appearance = {
          facial_features: {
            eyes: appearance.eyes || undefined,
            nose: appearance.nose || undefined,
            lips: appearance.lips || undefined,
            jawline: appearance.jawline || undefined,
            cheekbones: appearance.cheekbones || undefined,
          },
          hair: {
            color: appearance.hairColor || undefined,
            length: appearance.hairLength || undefined,
            style: appearance.hairStyle || undefined,
          },
          skin: {
            tone: appearance.skinTone || undefined,
            texture: appearance.skinTexture || undefined,
          },
        }
        params.pose = {
          position: pose.position || undefined,
          facial_expression: pose.expression || undefined,
          body_language: pose.bodyLanguage || undefined,
          looking_direction: pose.lookingDirection || undefined,
        }
        params.setting = {
          location_type: setting.locationType || undefined,
          specific_location: setting.specificLocation || undefined,
          lighting_conditions: setting.lighting || undefined,
          time_of_day: setting.timeOfDay || undefined,
        }
      }
      
      const response = await backendAPI.buildPrompt(params)
      if (response.success) {
        setGeneratedPrompt(response.data.prompt)
        setGeneratedNegative(response.data.negative_prompt)
        if (onPromptGenerated) {
          onPromptGenerated(response.data.prompt, response.data.negative_prompt)
        }
      }
    } catch (error: any) {
      console.error('Failed to build prompt:', error)
      alert('Failed to build prompt: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsGenerating(false)
    }
  }

  const handleOptimize = async () => {
    if (!promptToOptimize.trim()) {
      alert('Please enter a prompt to optimize')
      return
    }
    
    setIsGenerating(true)
    try {
      const response = await backendAPI.optimizePrompt(promptToOptimize)
      if (response.success) {
        setOptimizedPrompt(response.data.optimized)
      }
    } catch (error: any) {
      console.error('Failed to optimize prompt:', error)
      alert('Failed to optimize prompt: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wand2 className="h-5 w-5" />
          Advanced Prompt Engineering
        </CardTitle>
        <CardDescription>
          Build optimized prompts using advanced techniques
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="simple">Simple</TabsTrigger>
            <TabsTrigger value="advanced">Advanced</TabsTrigger>
            <TabsTrigger value="optimize">Optimize</TabsTrigger>
          </TabsList>

          <TabsContent value="simple" className="space-y-4">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Base Prompt (Optional)</label>
                <Textarea
                  placeholder="Enter base prompt or leave empty to use character config"
                  value={basePrompt}
                  onChange={(e) => setBasePrompt(e.target.value)}
                  className="min-h-[100px]"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Variation</label>
                  <Select value={variation} onValueChange={setVariation}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">Default</SelectItem>
                      <SelectItem value="portrait">Portrait</SelectItem>
                      <SelectItem value="sitting">Sitting</SelectItem>
                      <SelectItem value="lifestyle">Lifestyle</SelectItem>
                      <SelectItem value="boudoir">Boudoir</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="text-sm font-medium mb-2 block">Platform</label>
                  <Select value={platform} onValueChange={setPlatform}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select platform" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {Object.keys(platforms).map((key) => (
                        <SelectItem key={key} value={key}>
                          {platforms[key].name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button
                onClick={handleBuildPrompt}
                disabled={isGenerating}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Building...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Build Prompt
                  </>
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="advanced" className="space-y-4">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Age</label>
                  <Input
                    type="number"
                    value={subject.age}
                    onChange={(e) => setSubject({ ...subject, age: e.target.value })}
                    placeholder="25"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Gender</label>
                  <Input
                    value={subject.gender}
                    onChange={(e) => setSubject({ ...subject, gender: e.target.value })}
                    placeholder="woman"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Ethnicity</label>
                  <Input
                    value={subject.ethnicity}
                    onChange={(e) => setSubject({ ...subject, ethnicity: e.target.value })}
                    placeholder="mixed heritage"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Build</label>
                  <Input
                    value={subject.build}
                    onChange={(e) => setSubject({ ...subject, build: e.target.value })}
                    placeholder="athletic"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Facial Features</label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    value={appearance.eyes}
                    onChange={(e) => setAppearance({ ...appearance, eyes: e.target.value })}
                    placeholder="eyes"
                  />
                  <Input
                    value={appearance.nose}
                    onChange={(e) => setAppearance({ ...appearance, nose: e.target.value })}
                    placeholder="nose"
                  />
                  <Input
                    value={appearance.lips}
                    onChange={(e) => setAppearance({ ...appearance, lips: e.target.value })}
                    placeholder="lips"
                  />
                  <Input
                    value={appearance.jawline}
                    onChange={(e) => setAppearance({ ...appearance, jawline: e.target.value })}
                    placeholder="jawline"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Hair</label>
                <div className="grid grid-cols-3 gap-2">
                  <Input
                    value={appearance.hairColor}
                    onChange={(e) => setAppearance({ ...appearance, hairColor: e.target.value })}
                    placeholder="color"
                  />
                  <Input
                    value={appearance.hairLength}
                    onChange={(e) => setAppearance({ ...appearance, hairLength: e.target.value })}
                    placeholder="length"
                  />
                  <Input
                    value={appearance.hairStyle}
                    onChange={(e) => setAppearance({ ...appearance, hairStyle: e.target.value })}
                    placeholder="style"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Pose & Action</label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    value={pose.position}
                    onChange={(e) => setPose({ ...pose, position: e.target.value })}
                    placeholder="position (standing, sitting)"
                  />
                  <Input
                    value={pose.expression}
                    onChange={(e) => setPose({ ...pose, expression: e.target.value })}
                    placeholder="facial expression"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Platform</label>
                <Select value={platform} onValueChange={setPlatform}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select platform" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">None</SelectItem>
                    {Object.keys(platforms).map((key) => (
                      <SelectItem key={key} value={key}>
                        {platforms[key].name}
                      </SelectItem>
                    ))}
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
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Building...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Build Prompt
                  </>
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="optimize" className="space-y-4">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Prompt to Optimize</label>
                <Textarea
                  value={promptToOptimize}
                  onChange={(e) => setPromptToOptimize(e.target.value)}
                  placeholder="Enter prompt to optimize..."
                  className="min-h-[120px]"
                />
              </div>

              <Button
                onClick={handleOptimize}
                disabled={isGenerating || !promptToOptimize.trim()}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Optimizing...
                  </>
                ) : (
                  <>
                    <Wand2 className="mr-2 h-4 w-4" />
                    Optimize Prompt
                  </>
                )}
              </Button>

              {optimizedPrompt && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Optimized Prompt</label>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCopy(optimizedPrompt)}
                    >
                      {copied ? (
                        <>
                          <Check className="mr-2 h-4 w-4" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="mr-2 h-4 w-4" />
                          Copy
                        </>
                      )}
                    </Button>
                  </div>
                  <Textarea
                    value={optimizedPrompt}
                    readOnly
                    className="min-h-[120px]"
                  />
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {(generatedPrompt || generatedNegative) && (
          <div className="mt-6 space-y-4 pt-6 border-t">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Generated Prompt</label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopy(generatedPrompt)}
                >
                  {copied ? (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="mr-2 h-4 w-4" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
              <Textarea
                value={generatedPrompt}
                readOnly
                className="min-h-[100px]"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Negative Prompt</label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopy(generatedNegative)}
                >
                  {copied ? (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="mr-2 h-4 w-4" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
              <Textarea
                value={generatedNegative}
                readOnly
                className="min-h-[80px]"
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
