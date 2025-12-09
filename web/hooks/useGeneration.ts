'use client'

import { useState, useCallback, useRef } from 'react'
import { backendAPI } from '@/lib/api/backend'
import type { GenerationParams, GenerationProgress, GenerationResult } from '@/types/generation'

interface TroubleshootingInfo {
  error_code?: string
  troubleshooting?: {
    title?: string
    solutions?: string[]
  }
}

export function useImageGeneration() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState<GenerationProgress | null>(null)
  const [results, setResults] = useState<GenerationResult[]>([])
  const [error, setError] = useState<string | null>(null)
  const [troubleshootingInfo, setTroubleshootingInfo] = useState<TroubleshootingInfo | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const lastProgressRef = useRef<number>(0)


  const generate = useCallback(async (params: GenerationParams) => {
    setIsGenerating(true)
    setProgress(null)
    setError(null)
    setResults([])

    try {
      console.log('Starting generation with params:', params)
      console.log('Face consistency config:', params.faceConsistency)

      // Call backend API instead of ComfyUI directly
      // Backend will handle workflow building and face consistency
      const response = await backendAPI.generateImage({
        prompt: params.prompt,
        negative_prompt: params.negativePrompt,
        character_id: params.characterId,
        settings: {
          width: params.width,
          height: params.height,
          steps: params.steps,
          cfg_scale: params.cfg,
          sampler: params.sampler,
          seed: params.seed,
        },
        face_consistency: params.faceConsistency ? {
          enabled: params.faceConsistency.enabled,
          method: params.faceConsistency.method,
          strength: params.faceConsistency.strength,
          face_reference_path: params.faceConsistency.faceReferencePath,
          multiple_references: params.faceConsistency.multipleReferences,
          lora_name: params.faceConsistency.loraName,
          ip_method: params.faceConsistency.ipMethod,
          controlnet_strength: params.faceConsistency.controlnetStrength,
          ip_adapter_scale: params.faceConsistency.ipAdapterScale,
        } : undefined,
        post_processing: params.postProcessing ? {
          enabled: params.postProcessing.enabled,
          upscale: params.postProcessing.upscale,
          upscale_factor: params.postProcessing.upscale_factor,
          face_restoration: params.postProcessing.face_restoration,
          color_correction: params.postProcessing.color_correction,
          noise_reduction: params.postProcessing.noise_reduction,
          remove_metadata: params.postProcessing.remove_metadata,
          quality_optimization: params.postProcessing.quality_optimization,
          output_format: params.postProcessing.output_format,
          quality: params.postProcessing.quality,
        } : undefined,
        anti_detection: params.antiDetection ? {
          enabled: params.antiDetection.enabled,
          remove_metadata: params.antiDetection.remove_metadata,
          add_imperfections: params.antiDetection.add_imperfections,
          vary_quality: params.antiDetection.vary_quality,
          remove_ai_signatures: params.antiDetection.remove_ai_signatures,
          add_realistic_noise: params.antiDetection.add_realistic_noise,
          normalize_colors: params.antiDetection.normalize_colors,
        } : undefined,
        quality_check: params.qualityCheck ? {
          enabled: params.qualityCheck.enabled,
          min_score: params.qualityCheck.min_score,
        } : undefined,
      })

      if (!response.success || !response.data.job_id) {
        const errorInfo = (response as any)?.error
        const errorMessage = errorInfo?.message || 'Failed to start generation'
        const troubleshootingCode = errorInfo?.troubleshooting_code
        
        // Get troubleshooting info if error code is available
        if (troubleshootingCode) {
          try {
            const troubleshooting = errorInfo?.troubleshooting
            if (troubleshooting) {
              setTroubleshootingInfo({
                error_code: troubleshootingCode,
                troubleshooting: troubleshooting
              })
            } else {
              // Fetch full troubleshooting info
              const troubleshootingResponse = await backendAPI.getErrorResolution(troubleshootingCode)
              if (troubleshootingResponse.success && troubleshootingResponse.data) {
                setTroubleshootingInfo({
                  error_code: troubleshootingCode,
                  troubleshooting: {
                    title: troubleshootingResponse.data.title,
                    solutions: troubleshootingResponse.data.solutions
                  }
                })
              }
            }
          } catch (err) {
            console.warn('Failed to fetch troubleshooting info:', err)
          }
        }
        
        throw new Error(errorMessage)
      }

      const jobId = response.data.job_id
      console.log('Generation job created with ID:', jobId)

      // Clean up any existing polling
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }

      // Poll backend for job status
      const startPolling = async () => {
        if (pollingIntervalRef.current) return // Already polling
        
        console.log('Starting polling for job status...')
        let pollCount = 0
        lastProgressRef.current = 0
        
        pollingIntervalRef.current = setInterval(async () => {
          try {
            pollCount++
            
            // Poll backend for job status
            const statusResponse = await backendAPI.getImageStatus(jobId)
            
            if (!statusResponse.success || !statusResponse.data) {
              console.warn(`[Poll ${pollCount}] Failed to get job status`)
              return
            }
            
            const jobStatus = statusResponse.data
            
            // Log every 5th poll to reduce noise
            if (pollCount % 5 === 0) {
              console.log(`[Poll ${pollCount}] Job status: ${jobStatus.status}, progress: ${(jobStatus.progress * 100).toFixed(0)}%`)
            }
            
            // Update progress
            const progressValue = (jobStatus.progress || 0) * 100
            lastProgressRef.current = progressValue
            
            setProgress({
              promptId: jobId,
              status: jobStatus.status as any,
              progress: progressValue,
            })
            
            // Check if completed
            if (jobStatus.status === 'completed') {
              console.log('✅ Generation completed!')
              setIsGenerating(false)
              if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current)
                pollingIntervalRef.current = null
              }
              
              // Fetch results from backend
              if (jobStatus.media_id) {
                await fetchResultsFromBackend(jobStatus.media_id, jobId)
              } else {
                setError('Generation completed but no media ID found')
              }
              return
            }
            
            // Check if failed
            if (jobStatus.status === 'failed') {
              const errorMessage = jobStatus.error || jobStatus.error_message || 'Generation failed'
              console.error('Generation failed:', errorMessage)
              
              // Try to get error code from job metadata if available
              const errorCode = (jobStatus as any)?.error_code || (jobStatus as any)?.metadata?.error_code
              if (errorCode) {
                try {
                  const troubleshootingResponse = await backendAPI.diagnoseError(errorCode, errorMessage)
                  if (troubleshootingResponse.success && troubleshootingResponse.data) {
                    setTroubleshootingInfo({
                      error_code: errorCode,
                      troubleshooting: {
                        title: troubleshootingResponse.data.resolution?.title,
                        solutions: troubleshootingResponse.data.resolution?.solutions
                      }
                    })
                  }
                } catch (err) {
                  console.warn('Failed to fetch troubleshooting info:', err)
                }
              }
              
              setError(errorMessage)
              setIsGenerating(false)
              if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current)
                pollingIntervalRef.current = null
              }
              return
            }
            
            // Still processing
            if (jobStatus.status === 'processing') {
              setProgress({
                promptId: jobId,
                status: 'running',
                progress: progressValue,
              })
            } else if (jobStatus.status === 'pending') {
              setProgress({
                promptId: jobId,
                status: 'queued',
                progress: 0,
              })
            }
          } catch (err) {
            console.error('Polling error:', err)
            // Don't stop polling on error, just log it
          }
        }, 2000) // Poll every 2 seconds
      }

      // Start polling immediately
      startPolling()

      lastProgressRef.current = 0
      setProgress({
        promptId: jobId,
        status: 'queued',
        progress: 0,
      })
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to start generation'
      
      // Check if error response has troubleshooting info
      if (err.response?.data?.error?.troubleshooting_code) {
        const troubleshootingCode = err.response.data.error.troubleshooting_code
        try {
          const troubleshootingResponse = await backendAPI.diagnoseError(troubleshootingCode, errorMessage)
          if (troubleshootingResponse.success && troubleshootingResponse.data) {
            setTroubleshootingInfo({
              error_code: troubleshootingCode,
              troubleshooting: {
                title: troubleshootingResponse.data.resolution?.title,
                solutions: troubleshootingResponse.data.resolution?.solutions
              }
            })
          }
        } catch (troubleshootingErr) {
          console.warn('Failed to fetch troubleshooting info:', troubleshootingErr)
        }
      }
      
      setError(errorMessage)
      setIsGenerating(false)
      // Clean up on error
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }
  }, [])

  const fetchResultsFromBackend = useCallback(async (mediaId: string, jobId: string) => {
    try {
      console.log('Fetching results from backend for media:', mediaId)
      
      // Get media item from backend
      const mediaResponse = await backendAPI.getMedia(mediaId)
      
      if (!mediaResponse.success || !mediaResponse.data) {
        throw new Error('Failed to fetch media from backend')
      }
      
      const media = mediaResponse.data
      
      // Build download URL
      const imageUrl = backendAPI.getMediaDownloadUrl(mediaId)
      
      const result: GenerationResult = {
        id: media.id,
        promptId: jobId,
        imageUrl,
        thumbnailUrl: media.thumbnail_path ? backendAPI.getMediaDownloadUrl(media.id) : undefined,
        mediaId: media.id,
        metadata: {
          prompt: '', // Will be filled from job if needed
          cfg: 7,
          steps: 30,
          seed: 0,
          width: media.width || 1024,
          height: media.height || 1024,
          sampler: 'euler',
          model: '',
          timestamp: media.created_at || new Date().toISOString(),
        },
        createdAt: media.created_at || new Date().toISOString(),
      }
      
      console.log('✅ Result fetched from backend')
      setResults([result])
    } catch (err) {
      console.error('Failed to fetch results from backend:', err)
      setError('Failed to fetch generated image. Check backend media library.')
    }
  }, [])

  return {
    generate,
    isGenerating,
    progress,
    results,
    error,
    troubleshootingInfo,
  }
}

// Workflow building is now handled by the backend
// The backend service will:
// 1. Build the ComfyUI workflow
// 2. Apply face consistency if configured
// 3. Queue the prompt to ComfyUI
// 4. Monitor progress and save results
