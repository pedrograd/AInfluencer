'use client'

import { VideoGenerator } from '@/components/generation/VideoGenerator'

export default function VideoGenerationPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Generate Video</h1>
        <p className="text-muted-foreground">
          Create ultra-realistic videos with AI using AnimateDiff, SVD, and more
        </p>
      </div>
      <VideoGenerator />
    </div>
  )
}
