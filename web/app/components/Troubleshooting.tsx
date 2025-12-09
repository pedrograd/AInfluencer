'use client'

import { useState, useEffect } from 'react'
import { backendAPI } from '@/lib/api/backend'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface DiagnosticResult {
  timestamp?: string
  system?: any
  gpu?: any
  python?: any
  disk?: any
  comfyui?: any
  memory?: any
}

interface ErrorCode {
  code: string
  title: string
  description: string
  solutions: string[]
  diagnostic_commands?: string[]
  severity: string
}

interface ErrorResolution {
  error_code: string
  error_message: string
  resolution: {
    title: string
    description: string
    solutions: string[]
    severity: string
  }
  diagnostics: any
  timestamp: string
}

export default function Troubleshooting() {
  const [diagnostics, setDiagnostics] = useState<DiagnosticResult | null>(null)
  const [errorCodes, setErrorCodes] = useState<ErrorCode[]>([])
  const [selectedErrorCode, setSelectedErrorCode] = useState<string | null>(null)
  const [errorResolution, setErrorResolution] = useState<ErrorResolution | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [diagnosticError, setDiagnosticError] = useState<string | null>(null)

  // Load error codes on mount
  useEffect(() => {
    loadErrorCodes()
  }, [])

  const loadErrorCodes = async () => {
    try {
      const response = await backendAPI.listErrorCodes()
      if (response.success && response.data?.error_codes) {
        setErrorCodes(response.data.error_codes)
      }
    } catch (err: any) {
      console.error('Failed to load error codes:', err)
    }
  }

  const runDiagnostics = async () => {
    setLoading(true)
    setDiagnosticError(null)
    try {
      const response = await backendAPI.runDiagnostics()
      if (response.success && response.data) {
        setDiagnostics(response.data)
      } else {
        setDiagnosticError('Failed to run diagnostics')
      }
    } catch (err: any) {
      setDiagnosticError(err.message || 'Failed to run diagnostics')
    } finally {
      setLoading(false)
    }
  }

  const diagnoseError = async (errorCode: string, errorMessage?: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await backendAPI.diagnoseError(errorCode, errorMessage)
      if (response.success && response.data) {
        setErrorResolution(response.data)
      } else {
        setError('Failed to diagnose error')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to diagnose error')
    } finally {
      setLoading(false)
    }
  }

  const handleErrorCodeSelect = (code: string) => {
    setSelectedErrorCode(code)
    diagnoseError(code)
  }

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'text-red-600 dark:text-red-400'
      case 'high':
        return 'text-orange-600 dark:text-orange-400'
      case 'medium':
        return 'text-yellow-600 dark:text-yellow-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getSeverityBadge = (severity: string) => {
    const color = getSeverityColor(severity)
    return (
      <span className={`px-2 py-1 rounded text-xs font-semibold ${color} bg-opacity-10`}>
        {severity?.toUpperCase() || 'UNKNOWN'}
      </span>
    )
  }

  return (
    <section id="troubleshooting" className="section" style={{ background: 'var(--bg-secondary)' }}>
      <div className="container py-12">
        <div className="mb-8">
          <h2 className="text-4xl font-bold mb-4">Troubleshooting Guide</h2>
          <p className="text-lg text-muted-foreground">
            Comprehensive troubleshooting and diagnostic tools for the AInfluencer platform.
          </p>
        </div>

        <Tabs defaultValue="diagnostics" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="diagnostics">System Diagnostics</TabsTrigger>
            <TabsTrigger value="error-codes">Error Codes</TabsTrigger>
            <TabsTrigger value="common-issues">Common Issues</TabsTrigger>
          </TabsList>

          <TabsContent value="diagnostics" className="space-y-6">
            <Card className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-2xl font-semibold">System Diagnostics</h3>
                <Button onClick={runDiagnostics} disabled={loading}>
                  {loading ? 'Running...' : 'Run Diagnostics'}
                </Button>
              </div>

              {diagnosticError && (
                <Alert variant="destructive" className="mb-4">
                  <AlertDescription>{diagnosticError}</AlertDescription>
                </Alert>
              )}

              {diagnostics && (
                <div className="space-y-4 mt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* GPU Info */}
                    {diagnostics.gpu && (
                      <Card className="p-4">
                        <h4 className="font-semibold mb-2">GPU</h4>
                        <div className="space-y-1 text-sm">
                          <div>
                            <span className="font-medium">Available:</span>{' '}
                            {diagnostics.gpu.available ? (
                              <span className="text-green-600">Yes</span>
                            ) : (
                              <span className="text-red-600">No</span>
                            )}
                          </div>
                          {diagnostics.gpu.name && (
                            <div>
                              <span className="font-medium">Name:</span> {diagnostics.gpu.name}
                            </div>
                          )}
                          {diagnostics.gpu.memory_total && (
                            <div>
                              <span className="font-medium">Memory:</span>{' '}
                              {diagnostics.gpu.memory_total} GB
                            </div>
                          )}
                          {diagnostics.gpu.driver_version && (
                            <div>
                              <span className="font-medium">Driver:</span>{' '}
                              {diagnostics.gpu.driver_version}
                            </div>
                          )}
                          <div>
                            <span className="font-medium">CUDA Available:</span>{' '}
                            {diagnostics.gpu.cuda_available ? (
                              <span className="text-green-600">Yes</span>
                            ) : (
                              <span className="text-red-600">No</span>
                            )}
                          </div>
                        </div>
                      </Card>
                    )}

                    {/* Python Info */}
                    {diagnostics.python && (
                      <Card className="p-4">
                        <h4 className="font-semibold mb-2">Python</h4>
                        <div className="space-y-1 text-sm">
                          <div>
                            <span className="font-medium">Version:</span>{' '}
                            {diagnostics.python.version_info?.major}.
                            {diagnostics.python.version_info?.minor}.
                            {diagnostics.python.version_info?.micro}
                          </div>
                          <div>
                            <span className="font-medium">Compatible:</span>{' '}
                            {diagnostics.python.compatible ? (
                              <span className="text-green-600">Yes</span>
                            ) : (
                              <span className="text-red-600">No</span>
                            )}
                          </div>
                          <div>
                            <span className="font-medium">Recommended:</span>{' '}
                            {diagnostics.python.recommended}
                          </div>
                        </div>
                      </Card>
                    )}

                    {/* Disk Info */}
                    {diagnostics.disk && (
                      <Card className="p-4">
                        <h4 className="font-semibold mb-2">Disk Space</h4>
                        <div className="space-y-1 text-sm">
                          {diagnostics.disk.total && (
                            <div>
                              <span className="font-medium">Total:</span>{' '}
                              {diagnostics.disk.total.toFixed(2)} GB
                            </div>
                          )}
                          {diagnostics.disk.free && (
                            <div>
                              <span className="font-medium">Free:</span>{' '}
                              {diagnostics.disk.free.toFixed(2)} GB
                            </div>
                          )}
                          {diagnostics.disk.percent_used && (
                            <div>
                              <span className="font-medium">Used:</span>{' '}
                              {diagnostics.disk.percent_used.toFixed(1)}%
                            </div>
                          )}
                        </div>
                      </Card>
                    )}

                    {/* ComfyUI Info */}
                    {diagnostics.comfyui && (
                      <Card className="p-4">
                        <h4 className="font-semibold mb-2">ComfyUI</h4>
                        <div className="space-y-1 text-sm">
                          <div>
                            <span className="font-medium">Running:</span>{' '}
                            {diagnostics.comfyui.running ? (
                              <span className="text-green-600">Yes</span>
                            ) : (
                              <span className="text-red-600">No</span>
                            )}
                          </div>
                          <div>
                            <span className="font-medium">Accessible:</span>{' '}
                            {diagnostics.comfyui.accessible ? (
                              <span className="text-green-600">Yes</span>
                            ) : (
                              <span className="text-red-600">No</span>
                            )}
                          </div>
                          <div>
                            <span className="font-medium">Port:</span> {diagnostics.comfyui.port}
                          </div>
                        </div>
                      </Card>
                    )}
                  </div>

                  {/* Memory Info */}
                  {diagnostics.memory && (
                    <Card className="p-4">
                      <h4 className="font-semibold mb-2">System Memory</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        {diagnostics.memory.total && (
                          <div>
                            <span className="font-medium">Total:</span>{' '}
                            {diagnostics.memory.total.toFixed(2)} GB
                          </div>
                        )}
                        {diagnostics.memory.available && (
                          <div>
                            <span className="font-medium">Available:</span>{' '}
                            {diagnostics.memory.available.toFixed(2)} GB
                          </div>
                        )}
                        {diagnostics.memory.used && (
                          <div>
                            <span className="font-medium">Used:</span>{' '}
                            {diagnostics.memory.used.toFixed(2)} GB
                          </div>
                        )}
                        {diagnostics.memory.percent && (
                          <div>
                            <span className="font-medium">Usage:</span>{' '}
                            {diagnostics.memory.percent.toFixed(1)}%
                          </div>
                        )}
                      </div>
                    </Card>
                  )}
                </div>
              )}
            </Card>
          </TabsContent>

          <TabsContent value="error-codes" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-2xl font-semibold mb-4">Error Codes & Resolutions</h3>
              <p className="text-muted-foreground mb-6">
                Select an error code to view detailed resolution steps and diagnostics.
              </p>

              {error && (
                <Alert variant="destructive" className="mb-4">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {errorCodes.map((errorCode) => (
                  <Card
                    key={errorCode.code}
                    className={`p-4 cursor-pointer transition-colors ${
                      selectedErrorCode === errorCode.code
                        ? 'border-primary bg-primary/5'
                        : 'hover:bg-muted'
                    }`}
                    onClick={() => handleErrorCodeSelect(errorCode.code)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold">{errorCode.title}</h4>
                      {getSeverityBadge(errorCode.severity)}
                    </div>
                    <p className="text-sm text-muted-foreground">{errorCode.description}</p>
                    <div className="mt-2 text-xs text-muted-foreground">
                      Code: <code>{errorCode.code}</code>
                    </div>
                  </Card>
                ))}
              </div>

              {errorResolution && (
                <Card className="p-6 border-primary">
                  <h4 className="text-xl font-semibold mb-4">Resolution</h4>
                  <div className="space-y-4">
                    <div>
                      <h5 className="font-semibold mb-2">Description</h5>
                      <p className="text-muted-foreground">
                        {errorResolution.resolution.description}
                      </p>
                    </div>
                    <div>
                      <h5 className="font-semibold mb-2">Solutions</h5>
                      <ul className="list-disc list-inside space-y-2">
                        {errorResolution.resolution.solutions.map((solution, idx) => (
                          <li key={idx} className="text-muted-foreground">
                            {solution}
                          </li>
                        ))}
                      </ul>
                    </div>
                    {Object.keys(errorResolution.diagnostics || {}).length > 0 && (
                      <div>
                        <h5 className="font-semibold mb-2">Diagnostics</h5>
                        <pre className="bg-muted p-4 rounded text-xs overflow-auto">
                          {JSON.stringify(errorResolution.diagnostics, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </Card>
              )}
            </Card>
          </TabsContent>

          <TabsContent value="common-issues" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-2xl font-semibold mb-4">Common Issues & Solutions</h3>

              <div className="space-y-6">
                {/* Content Generation Fails */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-2">Content Generation Fails</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    Generation returns errors, no output produced, or process crashes.
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>Check GPU availability: <code>nvidia-smi</code></li>
                    <li>Verify model files exist</li>
                    <li>Check disk space</li>
                    <li>Review error logs</li>
                    <li>Restart services</li>
                  </ul>
                </Card>

                {/* Low Quality Output */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-2">Low Quality Output</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    Blurry images, artifacts present, or unrealistic appearance.
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>Increase resolution</li>
                    <li>Use more inference steps (30-50)</li>
                    <li>Use better quality models</li>
                    <li>Improve prompts with quality modifiers</li>
                    <li>Apply post-processing</li>
                  </ul>
                </Card>

                {/* Face Consistency Fails */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-2">Face Consistency Fails</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    Different faces in images, inconsistent appearance, or face doesn't match reference.
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>Check reference image quality (high resolution, clear face)</li>
                    <li>Increase face consistency strength</li>
                    <li>Verify method is applied</li>
                    <li>Use better face consistency method (IP-Adapter, InstantID)</li>
                    <li>Check face detection is working</li>
                  </ul>
                </Card>

                {/* GPU Not Detected */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-2">GPU Not Detected</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    nvidia-smi shows no GPU, CUDA not available, or models fail to load.
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>Check driver installation: <code>nvidia-smi</code></li>
                    <li>Verify CUDA: <code>nvcc --version</code></li>
                    <li>Check PyTorch CUDA: <code>python -c "import torch; print(torch.cuda.is_available())"</code></li>
                    <li>Reinstall PyTorch with CUDA if needed</li>
                  </ul>
                </Card>

                {/* Out of Memory */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-2">Out of Memory (OOM)</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    CUDA out of memory errors, generation fails, or system crashes.
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>Reduce batch size to 1</li>
                    <li>Generate at lower resolution (512x512) and upscale later</li>
                    <li>Clear GPU cache: <code>torch.cuda.empty_cache()</code></li>
                    <li>Enable CPU offloading if available</li>
                    <li>Close other GPU-intensive applications</li>
                  </ul>
                </Card>

                {/* Model Won't Load */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-2">Model Won't Load</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    Model file not found, loading errors, or corrupted model.
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>Check file exists: <code>ls -lh models/model.safetensors</code></li>
                    <li>Re-download model from source</li>
                    <li>Verify file format compatibility</li>
                    <li>Check file permissions</li>
                  </ul>
                </Card>

                {/* Slow Generation */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-2">Slow Generation</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    Generation takes too long or performance is poor.
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>Check GPU usage and ensure GPU is being used</li>
                    <li>Reduce inference steps (balance quality)</li>
                    <li>Use faster models</li>
                    <li>Enable optimizations</li>
                    <li>Check for CPU bottleneck</li>
                  </ul>
                </Card>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </section>
  )
}
