'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Loader2, 
  Cpu, 
  HardDrive, 
  MemoryStick,
  Download,
  Settings,
  Sparkles
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { backend } from '@/lib/api/backend'

interface SetupStatus {
  hardware: any
  nvidia_driver: any
  cuda: any
  cudnn: any
  python: any
  comfyui: any
  models: any
  face_consistency: any
  video_generation: any
  post_processing: any
  overall_status: string
}

export default function SetupPage() {
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    loadSetupStatus()
  }, [])

  const loadSetupStatus = async () => {
    try {
      setLoading(true)
      const response = await backend.get('/api/setup/verify')
      if (response.data.success) {
        setSetupStatus(response.data.data)
      }
    } catch (error) {
      console.error('Failed to load setup status:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: boolean, loading?: boolean) => {
    if (loading) {
      return <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
    }
    return status ? (
      <CheckCircle2 className="h-5 w-5 text-green-500" />
    ) : (
      <XCircle className="h-5 w-5 text-red-500" />
    )
  }

  const getStatusColor = (status: boolean) => {
    return status ? 'text-green-600' : 'text-red-600'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!setupStatus) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <AlertCircle className="h-12 w-12 text-red-500" />
        <p className="text-lg">Failed to load setup status</p>
        <Button onClick={loadSetupStatus}>Retry</Button>
      </div>
    )
  }

  const overallStatus = setupStatus.overall_status
  const overallColor = overallStatus === 'ready' ? 'text-green-600' : 
                      overallStatus === 'partial' ? 'text-yellow-600' : 
                      'text-red-600'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Setup</h1>
        <p className="text-muted-foreground">
          Verify your NVIDIA GPU setup and AI tools configuration
        </p>
      </div>

      {/* Overall Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5" />
            <span>Overall Status</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {overallStatus === 'ready' ? (
                <CheckCircle2 className={cn('h-8 w-8', overallColor)} />
              ) : overallStatus === 'partial' ? (
                <AlertCircle className={cn('h-8 w-8', overallColor)} />
              ) : (
                <XCircle className={cn('h-8 w-8', overallColor)} />
              )}
              <div>
                <p className={cn('text-2xl font-semibold', overallColor)}>
                  {overallStatus === 'ready' ? 'Ready' : 
                   overallStatus === 'partial' ? 'Partial Setup' : 
                   'Not Ready'}
                </p>
                <p className="text-sm text-muted-foreground">
                  {overallStatus === 'ready' ? 'System is ready for AI generation' :
                   overallStatus === 'partial' ? 'Some components need setup' :
                   'System setup required'}
                </p>
              </div>
            </div>
            <Button onClick={loadSetupStatus} variant="outline">
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="hardware">Hardware</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="tools">Tools</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">GPU & Drivers</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">GPU Available</span>
                  {getStatusIcon(setupStatus.hardware?.gpu_available)}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">NVIDIA Driver</span>
                  {getStatusIcon(setupStatus.nvidia_driver?.installed)}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">CUDA</span>
                  {getStatusIcon(setupStatus.cuda?.installed)}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">cuDNN</span>
                  {getStatusIcon(setupStatus.cudnn?.installed)}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Software</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Python</span>
                  {getStatusIcon(setupStatus.python?.meets_requirements)}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">ComfyUI</span>
                  {getStatusIcon(setupStatus.comfyui?.installed)}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Models Installed</span>
                  <span className="text-sm font-medium">
                    {setupStatus.models?.checkpoints?.length || 0}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="hardware" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Cpu className="h-5 w-5" />
                <span>Hardware Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {setupStatus.hardware?.gpu_name && (
                <div>
                  <p className="text-sm font-medium mb-1">GPU Name</p>
                  <p className="text-lg">{setupStatus.hardware.gpu_name}</p>
                </div>
              )}
              {setupStatus.hardware?.gpu_memory_total && (
                <div>
                  <p className="text-sm font-medium mb-1">GPU Memory</p>
                  <p className="text-lg">
                    {setupStatus.hardware.gpu_memory_total.toFixed(1)} GB Total
                    {setupStatus.hardware.gpu_memory_free && (
                      <span className="text-muted-foreground ml-2">
                        ({setupStatus.hardware.gpu_memory_free.toFixed(1)} GB Free)
                      </span>
                    )}
                  </p>
                </div>
              )}
              {setupStatus.hardware?.system_ram && (
                <div>
                  <p className="text-sm font-medium mb-1">System RAM</p>
                  <p className="text-lg">{setupStatus.hardware.system_ram.toFixed(1)} GB</p>
                </div>
              )}
              {setupStatus.hardware?.storage_free && (
                <div>
                  <p className="text-sm font-medium mb-1">Available Storage</p>
                  <p className="text-lg">{setupStatus.hardware.storage_free.toFixed(1)} GB</p>
                </div>
              )}
              
              <div className="pt-4 border-t space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Meets Minimum Requirements</span>
                  {getStatusIcon(setupStatus.hardware?.meets_minimum)}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Meets Recommended Requirements</span>
                  {getStatusIcon(setupStatus.hardware?.meets_recommended)}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>NVIDIA Driver</CardTitle>
            </CardHeader>
            <CardContent>
              {setupStatus.nvidia_driver?.installed ? (
                <div>
                  <p className="text-sm font-medium mb-1">Version</p>
                  <p className="text-lg">{setupStatus.nvidia_driver.version || 'Unknown'}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Detected via: {setupStatus.nvidia_driver.check_method}
                  </p>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  NVIDIA driver not detected. Please install from{' '}
                  <a href="https://www.nvidia.com/Download/index.aspx" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    NVIDIA website
                  </a>
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>CUDA Toolkit</CardTitle>
            </CardHeader>
            <CardContent>
              {setupStatus.cuda?.installed ? (
                <div>
                  <p className="text-sm font-medium mb-1">Version</p>
                  <p className="text-lg">{setupStatus.cuda.version || 'Unknown'}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Detected via: {setupStatus.cuda.check_method}
                  </p>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  CUDA toolkit not detected. Download from{' '}
                  <a href="https://developer.nvidia.com/cuda-downloads" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    NVIDIA CUDA downloads
                  </a>
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Installed Models</span>
                <Button size="sm" variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Download Models
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {setupStatus.models?.checkpoints?.length > 0 ? (
                <div className="space-y-2">
                  {setupStatus.models.checkpoints.map((model: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <p className="font-medium">{model.name}</p>
                        <p className="text-sm text-muted-foreground">{model.size_gb} GB</p>
                      </div>
                      {model.is_recommended && (
                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                          Recommended
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No models installed. Please download models from the recommended list.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tools" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Face Consistency Tools</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">IP-Adapter</span>
                {getStatusIcon(setupStatus.face_consistency?.ip_adapter?.installed)}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">InstantID</span>
                {getStatusIcon(setupStatus.face_consistency?.instantid?.installed)}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">FaceID</span>
                {getStatusIcon(setupStatus.face_consistency?.faceid?.installed)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Video Generation Tools</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">AnimateDiff</span>
                {getStatusIcon(setupStatus.video_generation?.animatediff?.installed)}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Stable Video Diffusion</span>
                {getStatusIcon(setupStatus.video_generation?.stable_video_diffusion?.installed)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Post-Processing Tools</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Real-ESRGAN</span>
                {getStatusIcon(setupStatus.post_processing?.upscaling?.realesrgan_installed)}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">GFPGAN</span>
                {getStatusIcon(setupStatus.post_processing?.face_restoration?.gfpgan_installed)}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">CodeFormer</span>
                {getStatusIcon(setupStatus.post_processing?.face_restoration?.codeformer_installed)}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">ExifTool</span>
                {getStatusIcon(setupStatus.post_processing?.metadata_tools?.exiftool_available)}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
