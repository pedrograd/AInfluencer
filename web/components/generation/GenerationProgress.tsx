'use client'

import { Progress } from '@/components/ui/progress'
import { GenerationProgress as GenerationProgressType } from '@/types/generation'

interface GenerationProgressProps {
  progress: GenerationProgressType | null
}

export function GenerationProgress({ progress }: GenerationProgressProps) {
  if (!progress) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span>Initializing...</span>
          <span>0%</span>
        </div>
        <Progress value={0} />
      </div>
    )
  }

  const progressPercent = progress.progress || 0
  const statusLabels = {
    queued: 'Queued',
    running: 'Generating',
    completed: 'Completed',
    failed: 'Failed',
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">{statusLabels[progress.status]}</span>
          <span className="text-muted-foreground">{Math.round(progressPercent)}%</span>
        </div>
        <Progress value={progressPercent} className="h-2" />
      </div>
      
      {progress.status === 'queued' && (
        <p className="text-xs text-muted-foreground">Waiting in queue...</p>
      )}
      
      {progress.status === 'running' && progressPercent < 10 && (
        <p className="text-xs text-muted-foreground">Starting generation...</p>
      )}
      
      {progress.status === 'running' && progressPercent >= 10 && (
        <p className="text-xs text-muted-foreground">Processing image...</p>
      )}

      {progress.currentStep !== undefined && progress.totalSteps !== undefined && (
        <div className="text-sm text-muted-foreground">
          Step {progress.currentStep} of {progress.totalSteps}
        </div>
      )}

      {progress.preview && (
        <div className="mt-4">
          <img
            src={progress.preview}
            alt="Preview"
            className="w-full rounded-lg border"
          />
        </div>
      )}

      {progress.error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
          {progress.error}
        </div>
      )}
    </div>
  )
}
