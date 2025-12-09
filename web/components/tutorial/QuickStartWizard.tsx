'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import { CheckCircle2, ArrowRight } from 'lucide-react'

interface WizardStep {
  id: string
  title: string
  description: string
  component: React.ReactNode
}

export function QuickStartWizard({ onComplete }: { onComplete?: () => void }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [formData, setFormData] = useState({
    characterName: '',
    characterDescription: '',
    preferredStyle: '',
    targetPlatform: '',
    setupComplete: false
  })

  const steps: WizardStep[] = [
    {
      id: 'welcome',
      title: 'Welcome to AInfluencer',
      description: 'Let\'s get you started in just a few steps',
      component: (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            This wizard will help you set up your first character and generate your first image.
          </p>
          <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground">
            <li>Create your first character</li>
            <li>Configure generation settings</li>
            <li>Generate your first image</li>
          </ul>
        </div>
      )
    },
    {
      id: 'character',
      title: 'Create Your Character',
      description: 'Set up your first AI character',
      component: (
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Character Name</label>
            <Input
              value={formData.characterName}
              onChange={(e) => setFormData({ ...formData, characterName: e.target.value })}
              placeholder="Enter character name"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">Description</label>
            <Textarea
              value={formData.characterDescription}
              onChange={(e) => setFormData({ ...formData, characterDescription: e.target.value })}
              placeholder="Describe your character..."
              rows={4}
            />
          </div>
        </div>
      )
    },
    {
      id: 'style',
      title: 'Choose Style',
      description: 'Select your preferred generation style',
      component: (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {['Professional', 'Casual', 'Artistic', 'Realistic'].map((style) => (
              <Button
                key={style}
                variant={formData.preferredStyle === style ? 'default' : 'outline'}
                onClick={() => setFormData({ ...formData, preferredStyle: style })}
                className="h-20"
              >
                {style}
              </Button>
            ))}
          </div>
        </div>
      )
    },
    {
      id: 'platform',
      title: 'Target Platform',
      description: 'Where will you post this content?',
      component: (
        <div className="space-y-4">
          <div className="space-y-2">
            {['Instagram', 'OnlyFans', 'Twitter', 'Facebook', 'Other'].map((platform) => (
              <div key={platform} className="flex items-center space-x-2">
                <Checkbox
                  id={platform}
                  checked={formData.targetPlatform === platform}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setFormData({ ...formData, targetPlatform: platform })
                    }
                  }}
                />
                <label htmlFor={platform} className="text-sm font-medium cursor-pointer">
                  {platform}
                </label>
              </div>
            ))}
          </div>
        </div>
      )
    },
    {
      id: 'complete',
      title: 'Setup Complete!',
      description: 'You\'re ready to start generating',
      component: (
        <div className="space-y-4 text-center">
          <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto" />
          <p className="text-sm text-muted-foreground">
            Your character has been created. You can now start generating images!
          </p>
        </div>
      )
    }
  ]

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      handleComplete()
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = () => {
    setFormData({ ...formData, setupComplete: true })
    onComplete?.()
  }

  const currentStepData = steps[currentStep]
  const progress = ((currentStep + 1) / steps.length) * 100

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>{currentStepData.title}</CardTitle>
        <CardDescription>{currentStepData.description}</CardDescription>
        <Progress value={progress} className="mt-4" />
      </CardHeader>
      <CardContent>
        <div className="mb-6">
          {currentStepData.component}
        </div>
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 0}
          >
            Previous
          </Button>
          <Button onClick={handleNext}>
            {currentStep === steps.length - 1 ? 'Complete Setup' : 'Next'}
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
