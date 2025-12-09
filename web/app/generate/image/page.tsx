'use client'

import { ImageGenerator } from '@/components/generation/ImageGenerator'
import { SimpleMode } from '@/components/generation/SimpleMode'
import { GenerationQueue } from '@/components/generation/GenerationQueue'

export default function ImageGenerationPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Generate Image</h1>
        <p className="text-muted-foreground">
          Create ultra-realistic images with AI using quick or advanced flows
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2 space-y-6">
          <ImageGenerator />
        </div>

        <div className="space-y-6">
          <SimpleMode />
          <GenerationQueue />
        </div>
      </div>
    </div>
  )
}
