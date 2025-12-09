'use client'

import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Upload, X, CheckCircle2, AlertCircle, Loader2, Info } from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import type { FaceConsistencyConfig, FaceQualityResult, FaceConsistencyMethodInfo } from '@/types/generation'
import api from '@/lib/api/backend'

interface FaceConsistencySettingsProps {
  config: FaceConsistencyConfig
  onChange: (config: FaceConsistencyConfig) => void
  characterId?: string
}

export function FaceConsistencySettings({
  config,
  onChange,
  characterId,
}: FaceConsistencySettingsProps) {
  const [preview, setPreview] = useState<string | null>(null)
  const [qualityResult, setQualityResult] = useState<FaceQualityResult | null>(null)
  const [validating, setValidating] = useState(false)
  const [availableMethods, setAvailableMethods] = useState<Record<string, FaceConsistencyMethodInfo>>({})
  const [loadingMethods, setLoadingMethods] = useState(true)

  // Load available methods
  useEffect(() => {
    const loadMethods = async () => {
      try {
        const response = await api.get('/api/face-consistency/methods')
        if (response.data.success) {
          setAvailableMethods(response.data.data)
        }
      } catch (error) {
        console.error('Failed to load face consistency methods:', error)
      } finally {
        setLoadingMethods(false)
      }
    }
    loadMethods()
  }, [])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      // Create preview
      const reader = new FileReader()
      reader.onload = () => {
        const result = reader.result as string
        setPreview(result)
      }
      reader.readAsDataURL(file)
      
      // Upload file to backend and get path
      // For now, use data URL as path (backend will handle file upload separately if needed)
      const result = reader.result as string
      setPreview(result)
      onChange({
        ...config,
        faceReferencePath: result, // Data URL for now, can be enhanced to use backend file path
      })
      
      // Validate quality
      validateQuality(file)
    }
  }, [config, onChange, characterId])

  const validateQuality = async (file: File) => {
    setValidating(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post('/api/face-consistency/validate', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      if (response.data.success) {
        setQualityResult(response.data.data)
      }
    } catch (error) {
      console.error('Quality validation failed:', error)
    } finally {
      setValidating(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp'],
    },
    maxFiles: 1,
  })

  const handleRemove = () => {
    setPreview(null)
    setQualityResult(null)
    onChange({
      ...config,
      faceReferencePath: undefined,
    })
  }

  const getMethodInfo = (method: string) => {
    return availableMethods[method] || null
  }

  const getStrengthLabel = (method: string) => {
    const methodInfo = getMethodInfo(method)
    if (!methodInfo) return 'Strength'
    
    switch (method) {
      case 'ip_adapter':
        return `IP-Adapter Strength (${methodInfo.consistency}/10 consistency)`
      case 'instantid':
        return `InstantID Strength (${methodInfo.consistency}/10 consistency)`
      case 'faceid':
        return `FaceID Strength (${methodInfo.consistency}/10 consistency)`
      case 'lora':
        return `LoRA Strength (${methodInfo.consistency}/10 consistency)`
      default:
        return 'Strength'
    }
  }

  const getStrengthDescription = (method: string) => {
    switch (method) {
      case 'ip_adapter':
        return '0.7-0.8: Balanced (recommended), 0.8-0.9: High consistency'
      case 'instantid':
        return '0.7-0.8: Balanced, 0.8-0.9: High consistency (recommended)'
      case 'faceid':
        return '0.7-0.9: Recommended range'
      case 'lora':
        return '0.7-1.0: Recommended range'
      default:
        return 'Adjust to control face consistency strength'
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Face Consistency</CardTitle>
        <CardDescription>
          Maintain the same character face across all generations
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Enable/Disable Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <label className="text-sm font-medium">Enable Face Consistency</label>
            <p className="text-xs text-muted-foreground">
              Use face consistency methods to maintain character identity
            </p>
          </div>
          <Button
            variant={config.enabled ? "default" : "outline"}
            size="sm"
            onClick={() => onChange({ ...config, enabled: !config.enabled })}
          >
            {config.enabled ? 'Enabled' : 'Disabled'}
          </Button>
        </div>

        {config.enabled && (
          <>
            {/* Method Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Method</label>
              <Select
                value={config.method}
                onValueChange={(value) => onChange({ ...config, method: value as any })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(availableMethods).map(([key, info]) => (
                    <SelectItem
                      key={key}
                      value={key}
                      disabled={!info.available}
                    >
                      <div className="flex items-center justify-between w-full">
                        <span>{info.name}</span>
                        {!info.available && (
                          <span className="text-xs text-muted-foreground ml-2">(Not installed)</span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {/* Method Info */}
              {getMethodInfo(config.method) && (
                <div className="text-xs text-muted-foreground space-y-1 p-2 bg-muted rounded">
                  <p><strong>Consistency:</strong> {getMethodInfo(config.method)?.consistency}/10</p>
                  <p><strong>Best for:</strong> {getMethodInfo(config.method)?.best_for}</p>
                  <p><strong>Speed:</strong> {getMethodInfo(config.method)?.speed.replace('_', ' ')}</p>
                </div>
              )}
            </div>

            {/* LoRA Name Input (for LoRA method) */}
            {config.method === 'lora' && (
              <div className="space-y-2">
                <label className="text-sm font-medium">LoRA Name</label>
                <input
                  type="text"
                  value={config.loraName || ''}
                  onChange={(e) => onChange({ ...config, loraName: e.target.value })}
                  placeholder="character_lora"
                  className="w-full px-3 py-2 border rounded-md"
                />
                <p className="text-xs text-muted-foreground">
                  Name of the LoRA file (without .safetensors extension)
                </p>
              </div>
            )}

            {/* Face Reference Upload (for reference-based methods) */}
            {config.method !== 'lora' && (
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Face Reference Image</label>
                  <p className="text-xs text-muted-foreground">
                    Upload a high-quality front-facing photo (1024x1024+ recommended)
                  </p>
                </div>

                {preview ? (
                  <div className="space-y-4">
                    <div className="relative">
                      <div className="relative aspect-square w-full overflow-hidden rounded-lg border">
                        <img
                          src={preview}
                          alt="Face reference"
                          className="h-full w-full object-cover"
                        />
                      </div>
                      <Button
                        variant="destructive"
                        size="icon"
                        className="absolute top-2 right-2"
                        onClick={handleRemove}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>

                    {/* Quality Validation Result */}
                    {validating && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Validating image quality...
                      </div>
                    )}

                    {qualityResult && !validating && (
                      <div className={cn(
                        "p-4 rounded-lg border",
                        qualityResult.is_valid ? "bg-green-50 border-green-200" : "bg-yellow-50 border-yellow-200"
                      )}>
                        <div className="flex items-start gap-2">
                          {qualityResult.is_valid ? (
                            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                          ) : (
                            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                          )}
                          <div className="flex-1 space-y-2">
                            <div>
                              <p className="text-sm font-medium">
                                Quality Score: {(qualityResult.quality_score * 100).toFixed(0)}%
                              </p>
                              {qualityResult.is_optimal && (
                                <p className="text-xs text-green-600">Optimal quality</p>
                              )}
                            </div>
                            
                            {qualityResult.issues.length > 0 && (
                              <div>
                                <p className="text-xs font-medium text-yellow-800">Issues:</p>
                                <ul className="text-xs text-yellow-700 list-disc list-inside">
                                  {qualityResult.issues.map((issue, i) => (
                                    <li key={i}>{issue}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {qualityResult.recommendations.length > 0 && (
                              <div>
                                <p className="text-xs font-medium">Recommendations:</p>
                                <ul className="text-xs text-muted-foreground list-disc list-inside">
                                  {qualityResult.recommendations.map((rec, i) => (
                                    <li key={i}>{rec}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div
                    {...getRootProps()}
                    className={cn(
                      'cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors',
                      isDragActive
                        ? 'border-primary bg-primary/5'
                        : 'border-muted-foreground/25 hover:border-primary/50'
                    )}
                  >
                    <input {...getInputProps()} />
                    <div className="flex flex-col items-center justify-center space-y-4">
                      <div className="rounded-full bg-muted p-4">
                        <Upload className="h-6 w-6 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">
                          {isDragActive ? 'Drop image here' : 'Upload face reference'}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Drag and drop or click to select (1024x1024+ recommended)
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Strength Control */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">
                  {getStrengthLabel(config.method)}
                </label>
                <span className="text-sm text-muted-foreground">
                  {config.strength.toFixed(2)}
                </span>
              </div>
              <Slider
                value={[config.strength]}
                onValueChange={(values) => onChange({ ...config, strength: values[0] })}
                min={0}
                max={1}
                step={0.05}
              />
              <p className="text-xs text-muted-foreground">
                {getStrengthDescription(config.method)}
              </p>
            </div>

            {/* Additional Settings for InstantID */}
            {config.method === 'instantid' && (
              <div className="space-y-4 p-4 bg-muted rounded-lg">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">ControlNet Strength</label>
                    <span className="text-sm text-muted-foreground">
                      {(config.controlnetStrength || 0.8).toFixed(2)}
                    </span>
                  </div>
                  <Slider
                    value={[config.controlnetStrength || 0.8]}
                    onValueChange={(values) => onChange({ ...config, controlnetStrength: values[0] })}
                    min={0}
                    max={1}
                    step={0.05}
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">IP-Adapter Scale</label>
                    <span className="text-sm text-muted-foreground">
                      {(config.ipAdapterScale || 0.8).toFixed(2)}
                    </span>
                  </div>
                  <Slider
                    value={[config.ipAdapterScale || 0.8]}
                    onValueChange={(values) => onChange({ ...config, ipAdapterScale: values[0] })}
                    min={0}
                    max={1}
                    step={0.05}
                  />
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
