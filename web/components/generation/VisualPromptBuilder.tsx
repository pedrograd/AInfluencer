'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { X, Plus } from 'lucide-react'

interface PromptComponent {
  id: string
  type: 'subject' | 'style' | 'quality' | 'setting' | 'pose' | 'lighting'
  value: string
}

export function VisualPromptBuilder({ onPromptGenerated }: { onPromptGenerated?: (prompt: string) => void }) {
  const [components, setComponents] = useState<PromptComponent[]>([])
  const [selectedType, setSelectedType] = useState<string>('subject')
  const [inputValue, setInputValue] = useState('')

  const componentOptions: Record<string, string[]> = {
    subject: ['woman', 'man', 'person', 'character', 'portrait'],
    style: ['professional', 'casual', 'artistic', 'realistic', 'cinematic'],
    quality: ['high quality', 'ultra realistic', '8k', 'detailed', 'sharp'],
    setting: ['studio', 'outdoor', 'indoor', 'beach', 'urban'],
    pose: ['standing', 'sitting', 'walking', 'portrait pose', 'natural'],
    lighting: ['natural lighting', 'studio lighting', 'golden hour', 'soft lighting', 'dramatic']
  }

  const addComponent = () => {
    if (!inputValue.trim()) return

    const newComponent: PromptComponent = {
      id: Date.now().toString(),
      type: selectedType as PromptComponent['type'],
      value: inputValue
    }

    setComponents([...components, newComponent])
    setInputValue('')
    generatePrompt([...components, newComponent])
  }

  const removeComponent = (id: string) => {
    const updated = components.filter(c => c.id !== id)
    setComponents(updated)
    generatePrompt(updated)
  }

  const generatePrompt = (comps: PromptComponent[]) => {
    const prompt = comps.map(c => c.value).join(', ')
    onPromptGenerated?.(prompt)
  }

  const quickAdd = (type: string, value: string) => {
    const newComponent: PromptComponent = {
      id: Date.now().toString(),
      type: type as PromptComponent['type'],
      value: value
    }
    const updated = [...components, newComponent]
    setComponents(updated)
    generatePrompt(updated)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Visual Prompt Builder</CardTitle>
        <CardDescription>
          Build prompts visually by adding components
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Select value={selectedType} onValueChange={setSelectedType}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="subject">Subject</SelectItem>
              <SelectItem value="style">Style</SelectItem>
              <SelectItem value="quality">Quality</SelectItem>
              <SelectItem value="setting">Setting</SelectItem>
              <SelectItem value="pose">Pose</SelectItem>
              <SelectItem value="lighting">Lighting</SelectItem>
            </SelectContent>
          </Select>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addComponent()}
            placeholder="Enter value..."
            className="flex-1 px-3 py-2 border rounded-md"
          />
          <Button onClick={addComponent} size="sm">
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Quick Add</label>
          <div className="flex flex-wrap gap-2">
            {componentOptions[selectedType]?.map((option) => (
              <Button
                key={option}
                variant="outline"
                size="sm"
                onClick={() => quickAdd(selectedType, option)}
              >
                {option}
              </Button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Prompt Components</label>
          <div className="flex flex-wrap gap-2 min-h-[60px] p-2 border rounded-md">
            {components.length > 0 ? (
              components.map((component) => (
                <Badge key={component.id} variant="secondary" className="flex items-center gap-1">
                  <span className="text-xs">{component.type}:</span>
                  <span>{component.value}</span>
                  <button
                    onClick={() => removeComponent(component.id)}
                    className="ml-1 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No components added yet</p>
            )}
          </div>
        </div>

        {components.length > 0 && (
          <div className="p-3 bg-secondary rounded-md">
            <p className="text-xs text-muted-foreground mb-1">Generated Prompt:</p>
            <p className="text-sm font-mono">{components.map(c => c.value).join(', ')}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
