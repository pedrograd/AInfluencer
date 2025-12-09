'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileText, Copy, Check } from 'lucide-react'

interface PromptTemplate {
  id: string
  name: string
  prompt: string
  category: string
}

interface PromptTemplatesProps {
  onTemplateSelected?: (prompt: string) => void
}

export function PromptTemplates({ onTemplateSelected }: PromptTemplatesProps) {
  const [templates, setTemplates] = useState<PromptTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | null>(null)
  const [copied, setCopied] = useState(false)

  const loadTemplates = async () => {
    try {
      // TODO: Implement template loading from backend
      // For now, use default templates
      const defaultTemplates: PromptTemplate[] = [
        {
          id: '1',
          name: 'Professional Portrait',
          prompt: 'professional portrait, high quality, studio lighting, detailed face, realistic skin texture, 8k, ultra realistic',
          category: 'portrait'
        },
        {
          id: '2',
          name: 'Lifestyle Casual',
          prompt: 'casual lifestyle photography, natural lighting, authentic moment, realistic, high quality, detailed',
          category: 'lifestyle'
        },
        {
          id: '3',
          name: 'Fashion Style',
          prompt: 'fashion photography, elegant pose, professional lighting, high fashion, detailed clothing, ultra realistic',
          category: 'fashion'
        }
      ]
      setTemplates(defaultTemplates)
    } catch (err) {
      console.error('Load templates error:', err)
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
        <CardTitle className="flex items-center space-x-2">
          <FileText className="h-5 w-5" />
          <span>Prompt Templates</span>
        </CardTitle>
        <CardDescription>
          Use pre-made prompt templates for quick generation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button onClick={loadTemplates} variant="outline" className="w-full">
          Load Templates
        </Button>

        {templates.length > 0 && (
          <div className="space-y-2">
            {templates.map((template) => (
              <div
                key={template.id}
                className="p-3 border rounded-md hover:bg-secondary transition-colors cursor-pointer"
                onClick={() => setSelectedTemplate(template)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-sm">{template.name}</p>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {template.prompt}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleCopy(template.prompt)
                      onTemplateSelected?.(template.prompt)
                    }}
                  >
                    {copied && selectedTemplate?.id === template.id ? (
                      <Check className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        {selectedTemplate && (
          <div className="p-4 bg-secondary rounded-md">
            <p className="text-sm font-medium mb-2">{selectedTemplate.name}</p>
            <p className="text-sm text-muted-foreground">{selectedTemplate.prompt}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
