'use client'

import { useCallback, useState } from 'react'
import { QuickStartWizard } from '@/components/tutorial/QuickStartWizard'
import { InteractiveTutorial } from '@/components/tutorial/InteractiveTutorial'
import { HelpCenter } from '@/components/help/HelpCenter'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Play, Sparkles } from 'lucide-react'

const tutorialSteps = [
  {
    id: 'dashboard',
    title: 'Dashboard overview',
    description: 'Check ComfyUI connection status and jump into quick actions.',
  },
  {
    id: 'generate',
    title: 'Generate content',
    description: 'Use Generate Image/Video pages for quick or advanced workflows.',
  },
  {
    id: 'prompts',
    title: 'Prompt lab',
    description: 'Leverage templates, history, and AI suggestions to refine prompts.',
  },
  {
    id: 'characters',
    title: 'Character management',
    description: 'Create characters and keep face consistency across generations.',
  },
  {
    id: 'help',
    title: 'Help & docs',
    description: 'Search guides, tutorials, and troubleshooting from one place.',
  },
]

export default function HelpPage() {
  const [showTutorial, setShowTutorial] = useState(false)

  const scrollToQuickStart = useCallback(() => {
    const el = document.getElementById('quickstart')
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' })
    }
  }, [])

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Help & Onboarding</h1>
          <p className="text-muted-foreground">
            Guided setup, interactive tutorials, and searchable help center.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => setShowTutorial(true)}>
            <Play className="mr-2 h-4 w-4" />
            Start interactive tutorial
          </Button>
          <Button variant="outline" onClick={scrollToQuickStart}>
            <Sparkles className="mr-2 h-4 w-4" />
            Jump to quick start
          </Button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2 space-y-6" id="quickstart">
          <Card>
            <CardHeader>
              <CardTitle>Quick Start Wizard</CardTitle>
            </CardHeader>
            <CardContent>
              <QuickStartWizard />
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Need a walkthrough?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>
                Use the interactive tutorial to learn the core flows: dashboard, generation,
                prompt lab, and character management.
              </p>
              <p>
                The tutorial can be relaunched anytime from this page if you want a refresher
                or to onboard teammates.
              </p>
            </CardContent>
          </Card>
          <HelpCenter />
        </div>
      </div>

      {showTutorial && (
        <InteractiveTutorial
          steps={tutorialSteps}
          onComplete={() => setShowTutorial(false)}
          onSkip={() => setShowTutorial(false)}
        />
      )}
    </div>
  )
}
