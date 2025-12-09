'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Save, X, Upload } from 'lucide-react'
import type { Character, CharacterFormData, CharacterTemplate } from '@/types/character'

interface CharacterFormProps {
  character?: Character | null
  templates?: Record<string, CharacterTemplate>
  onSave: (data: CharacterFormData) => Promise<void>
  onCancel: () => void
}

export function CharacterForm({ character, templates, onSave, onCancel }: CharacterFormProps) {
  const [formData, setFormData] = useState<CharacterFormData>({
    name: character?.name || '',
    age: character?.age,
    description: character?.description || '',
    persona: character?.persona || {},
    appearance: character?.appearance || {},
    style: character?.style || {},
    contentPreferences: character?.contentPreferences || {},
    consistencyRules: character?.consistencyRules || {},
  })
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [isSaving, setIsSaving] = useState(false)

  // Update form data when character changes
  useEffect(() => {
    if (character) {
      setFormData({
        name: character.name || '',
        age: character.age,
        description: character.description || '',
        persona: character.persona || {},
        appearance: character.appearance || {},
        style: character.style || {},
        contentPreferences: character.contentPreferences || {},
        consistencyRules: character.consistencyRules || {},
      })
      setSelectedTemplate('')
    } else {
      setFormData({
        name: '',
        age: undefined,
        description: '',
        persona: {},
        appearance: {},
        style: {},
        contentPreferences: {},
        consistencyRules: {},
      })
      setSelectedTemplate('')
    }
  }, [character])

  useEffect(() => {
    if (selectedTemplate && templates?.[selectedTemplate] && !character) {
      const template = templates[selectedTemplate]
      setFormData(prev => ({
        ...prev,
        persona: template.persona || prev.persona,
        appearance: template.appearance || prev.appearance,
        style: template.style || prev.style,
        contentPreferences: template.contentPreferences || prev.contentPreferences,
        consistencyRules: template.consistencyRules || prev.consistencyRules,
      }))
    }
  }, [selectedTemplate, templates, character])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    try {
      await onSave({ ...formData, template: selectedTemplate || undefined })
    } finally {
      setIsSaving(false)
    }
  }

  const updatePersona = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      persona: {
        ...prev.persona,
        [field]: value,
      },
    }))
  }

  const updateAppearance = (section: string, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      appearance: {
        ...prev.appearance,
        [section]: {
          ...(prev.appearance?.[section as keyof typeof prev.appearance] as any || {}),
          [field]: value,
        },
      },
    }))
  }

  const updateStyle = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      style: {
        ...prev.style,
        [field]: value,
      },
    }))
  }

  const updateContentPreferences = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      contentPreferences: {
        ...prev.contentPreferences,
        [field]: value,
      },
    }))
  }

  const updateConsistencyRules = (section: string, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      consistencyRules: {
        ...prev.consistencyRules,
        [section]: {
          ...(prev.consistencyRules?.[section as keyof typeof prev.consistencyRules] as any || {}),
          [field]: value,
        },
      },
    }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
          <CardDescription>Character name and basic details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="age">Age</Label>
            <Input
              id="age"
              type="number"
              value={formData.age || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, age: e.target.value ? parseInt(e.target.value) : undefined }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
            />
          </div>
          {templates && Object.keys(templates).length > 0 && (
            <div className="space-y-2">
              <Label htmlFor="template">Template (Optional)</Label>
              <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a template" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">None</SelectItem>
                  {Object.entries(templates).map(([key, template]) => (
                    <SelectItem key={key} value={key}>
                      {template.name || key}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detailed Sections */}
      <Tabs defaultValue="persona" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="persona">Persona</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="style">Style</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="consistency">Consistency</TabsTrigger>
        </TabsList>

        {/* Persona Tab */}
        <TabsContent value="persona" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Persona</CardTitle>
              <CardDescription>Personality, voice, and interests</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Personality Traits</Label>
                <Textarea
                  placeholder="confident, friendly, creative"
                  value={formData.persona?.personality?.traits?.join(', ') || ''}
                  onChange={(e) => updatePersona('personality', {
                    ...formData.persona?.personality,
                    traits: e.target.value.split(',').map(t => t.trim()).filter(Boolean),
                  })}
                  rows={2}
                />
              </div>
              <div className="space-y-2">
                <Label>Voice</Label>
                <Input
                  placeholder="casual and authentic"
                  value={formData.persona?.personality?.voice || ''}
                  onChange={(e) => updatePersona('personality', {
                    ...formData.persona?.personality,
                    voice: e.target.value,
                  })}
                />
              </div>
              <div className="space-y-2">
                <Label>Tone</Label>
                <Input
                  placeholder="warm and engaging"
                  value={formData.persona?.personality?.tone || ''}
                  onChange={(e) => updatePersona('personality', {
                    ...formData.persona?.personality,
                    tone: e.target.value,
                  })}
                />
              </div>
              <div className="space-y-2">
                <Label>Interests</Label>
                <Textarea
                  placeholder="fitness, travel, photography"
                  value={formData.persona?.interests?.join(', ') || ''}
                  onChange={(e) => updatePersona('interests', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
                  rows={2}
                />
              </div>
              <div className="space-y-2">
                <Label>Values</Label>
                <Textarea
                  placeholder="authenticity, self-improvement, community"
                  value={formData.persona?.values?.join(', ') || ''}
                  onChange={(e) => updatePersona('values', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance Tab */}
        <TabsContent value="appearance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>Physical characteristics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Face - Age</Label>
                <Input
                  type="number"
                  value={formData.appearance?.face?.age || ''}
                  onChange={(e) => updateAppearance('face', 'age', e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>
              <div className="space-y-2">
                <Label>Face - Ethnicity</Label>
                <Input
                  value={typeof formData.appearance?.face === 'object' ? formData.appearance.face.ethnicity || '' : ''}
                  onChange={(e) => updateAppearance('face', 'ethnicity', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Face - Eyes</Label>
                <Input
                  placeholder="large hazel eyes"
                  value={typeof formData.appearance?.face === 'object' && typeof formData.appearance.face.eyes === 'string' 
                    ? formData.appearance.face.eyes 
                    : typeof formData.appearance?.face?.eyes === 'object' 
                      ? `${formData.appearance.face.eyes.size || ''} ${formData.appearance.face.eyes.color || ''} ${formData.appearance.face.eyes.shape || ''} eyes`.trim()
                      : ''}
                  onChange={(e) => updateAppearance('face', 'eyes', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Hair - Color</Label>
                <Input
                  value={formData.appearance?.hair?.color || ''}
                  onChange={(e) => updateAppearance('hair', 'color', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Hair - Length & Style</Label>
                <Input
                  placeholder="shoulder-length wavy"
                  value={`${formData.appearance?.hair?.length || ''} ${formData.appearance?.hair?.style || ''}`.trim()}
                  onChange={(e) => {
                    const parts = e.target.value.split(' ')
                    updateAppearance('hair', 'length', parts[0] || '')
                    updateAppearance('hair', 'style', parts.slice(1).join(' ') || '')
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label>Body - Height</Label>
                <Input
                  value={formData.appearance?.body?.height || ''}
                  onChange={(e) => updateAppearance('body', 'height', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Body - Build</Label>
                <Input
                  placeholder="athletic, toned"
                  value={formData.appearance?.body?.build || ''}
                  onChange={(e) => updateAppearance('body', 'build', e.target.value)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Style Tab */}
        <TabsContent value="style" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Style Guide</CardTitle>
              <CardDescription>Visual style and aesthetic</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Photography Style</Label>
                <Input
                  placeholder="professional fashion photography"
                  value={formData.style?.photography || ''}
                  onChange={(e) => updateStyle('photography', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Color Palette - Primary</Label>
                <Input
                  placeholder="warm tones"
                  value={formData.style?.colorPalette?.primary || ''}
                  onChange={(e) => updateStyle('colorPalette', {
                    ...formData.style?.colorPalette,
                    primary: e.target.value,
                  })}
                />
              </div>
              <div className="space-y-2">
                <Label>Lighting</Label>
                <Input
                  placeholder="soft natural lighting"
                  value={formData.style?.lighting || ''}
                  onChange={(e) => updateStyle('lighting', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Mood</Label>
                <Input
                  placeholder="confident, aspirational, authentic"
                  value={formData.style?.mood || ''}
                  onChange={(e) => updateStyle('mood', e.target.value)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Content Preferences Tab */}
        <TabsContent value="content" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Content Preferences</CardTitle>
              <CardDescription>Content types and topics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Image Types</Label>
                <Textarea
                  placeholder="lifestyle photography, fashion photography"
                  value={formData.contentPreferences?.imageTypes?.join(', ') || ''}
                  onChange={(e) => updateContentPreferences('imageTypes', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
                  rows={2}
                />
              </div>
              <div className="space-y-2">
                <Label>Video Types</Label>
                <Textarea
                  placeholder="lifestyle vlogs, fashion content"
                  value={formData.contentPreferences?.videoTypes?.join(', ') || ''}
                  onChange={(e) => updateContentPreferences('videoTypes', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
                  rows={2}
                />
              </div>
              <div className="space-y-2">
                <Label>Topics</Label>
                <Textarea
                  placeholder="fashion, fitness, travel"
                  value={formData.contentPreferences?.topics?.join(', ') || ''}
                  onChange={(e) => updateContentPreferences('topics', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Consistency Rules Tab */}
        <TabsContent value="consistency" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Consistency Rules</CardTitle>
              <CardDescription>Rules for maintaining character consistency</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Face Method</Label>
                <Select
                  value={formData.consistencyRules?.face?.method || 'InstantID'}
                  onValueChange={(value) => updateConsistencyRules('face', 'method', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="InstantID">InstantID</SelectItem>
                    <SelectItem value="IP-Adapter">IP-Adapter</SelectItem>
                    <SelectItem value="FaceID">FaceID</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Face Strength (0.0 - 1.0)</Label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={formData.consistencyRules?.face?.strength || 0.8}
                  onChange={(e) => updateConsistencyRules('face', 'strength', parseFloat(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label>Style - Must Match</Label>
                <Select
                  value={formData.consistencyRules?.style?.mustMatch ? 'true' : 'false'}
                  onValueChange={(value) => updateConsistencyRules('style', 'mustMatch', value === 'true')}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="true">Yes</SelectItem>
                    <SelectItem value="false">No</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Face References Section */}
      {character && (
        <Card>
          <CardHeader>
            <CardTitle>Face References</CardTitle>
            <CardDescription>Upload face reference images for this character</CardDescription>
          </CardHeader>
          <CardContent>
            <FaceReferenceManager characterId={character.id} />
          </CardContent>
        </Card>
      )}

      {/* Form Actions */}
      <div className="flex justify-end space-x-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          <X className="mr-2 h-4 w-4" />
          Cancel
        </Button>
        <Button type="submit" disabled={isSaving}>
          <Save className="mr-2 h-4 w-4" />
          {isSaving ? 'Saving...' : 'Save Character'}
        </Button>
      </div>
    </form>
  )
}

// Face Reference Manager Component
function FaceReferenceManager({ characterId }: { characterId: string }) {
  const [faceRefs, setFaceRefs] = useState<any[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadFaceReferences()
  }, [characterId])

  const loadFaceReferences = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/characters/${characterId}`)
      const data = await response.json()
      if (data.success) {
        setFaceRefs(data.data.face_references || [])
      }
    } catch (error) {
      console.error('Failed to load face references:', error)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_BASE}/api/characters/${characterId}/face-references`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      if (data.success) {
        await loadFaceReferences()
      } else {
        alert('Failed to upload face reference: ' + (data.error || 'Unknown error'))
      }
    } catch (error) {
      console.error('Failed to upload face reference:', error)
      alert('Failed to upload face reference')
    } finally {
      setIsUploading(false)
      event.target.value = ''
    }
  }

  const handleDelete = async (faceRefId: string) => {
    if (!confirm('Are you sure you want to delete this face reference?')) {
      return
    }

    try {
      const response = await fetch(`${API_BASE}/api/characters/${characterId}/face-references/${faceRefId}`, {
        method: 'DELETE',
      })

      const data = await response.json()
      if (data.success) {
        await loadFaceReferences()
      } else {
        alert('Failed to delete face reference')
      }
    } catch (error) {
      console.error('Failed to delete face reference:', error)
      alert('Failed to delete face reference')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label htmlFor="face-ref-upload" className="cursor-pointer">
          <Button type="button" variant="outline" disabled={isUploading} asChild>
            <span>
              <Upload className="mr-2 h-4 w-4" />
              {isUploading ? 'Uploading...' : 'Upload Face Reference'}
            </span>
          </Button>
        </label>
        <input
          id="face-ref-upload"
          type="file"
          accept="image/*"
          onChange={handleFileUpload}
          className="hidden"
          disabled={isUploading}
        />
      </div>

      {faceRefs.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {faceRefs.map((ref) => (
            <div key={ref.id} className="relative group">
              <div className="aspect-square overflow-hidden rounded-lg border">
                <img
                  src={`${API_BASE}/api/characters/${characterId}/face-references/${ref.id}/image`}
                  alt="Face reference"
                  className="h-full w-full object-cover"
                />
              </div>
              <Button
                type="button"
                variant="destructive"
                size="icon"
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => handleDelete(ref.id)}
              >
                <X className="h-4 w-4" />
              </Button>
              <div className="mt-2 text-xs text-muted-foreground truncate">
                {ref.file_name}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-muted-foreground">
          <p>No face references uploaded yet</p>
          <p className="text-sm mt-2">Upload a high-quality front-facing photo (1024x1024+ recommended)</p>
        </div>
      )}
    </div>
  )
}
