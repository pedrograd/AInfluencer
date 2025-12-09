'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { antiDetectionAPI } from '@/lib/api/antiDetection'
import { Shield, Upload, TestTube } from 'lucide-react'

export default function AntiDetectionPage() {
  const [file, setFile] = useState<File | null>(null)
  const [config, setConfig] = useState({
    remove_metadata: true,
    add_imperfections: true,
    vary_quality: true,
    remove_ai_signatures: true,
    add_realistic_noise: false,
    normalize_colors: true,
  })
  const [isProcessing, setIsProcessing] = useState(false)
  const [testResults, setTestResults] = useState<any>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleProcess = async () => {
    if (!file) {
      alert('Please select a file')
      return
    }

    setIsProcessing(true)
    try {
      const response = await antiDetectionAPI.process({
        image_path: `/tmp/${file.name}`,
        config,
      })

      if (response.success) {
        alert('✅ Anti-detection processing completed!')
      }
    } catch (error) {
      console.error('Error processing:', error)
      alert('Failed to process. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleTest = async () => {
    if (!file) {
      alert('Please select a file')
      return
    }

    setIsProcessing(true)
    try {
      const response = await antiDetectionAPI.test({
        image_path: `/tmp/${file.name}`,
        detection_tools: ['hive', 'sensity', 'ai_or_not'],
      })

      if (response.success) {
        setTestResults(response.data)
      }
    } catch (error) {
      console.error('Error testing:', error)
      alert('Failed to test. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Shield className="h-8 w-8" />
          Anti-Detection
        </h1>
        <p className="text-muted-foreground">
          Make content undetectable as AI-generated
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Process Image</CardTitle>
            <CardDescription>
              Apply anti-detection techniques to make content undetectable
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="file">Select Image</Label>
              <Input
                id="file"
                type="file"
                accept="image/*"
                onChange={handleFileChange}
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="remove-metadata">Remove Metadata (Critical)</Label>
                <Switch
                  id="remove-metadata"
                  checked={config.remove_metadata}
                  onCheckedChange={(checked) => setConfig({ ...config, remove_metadata: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="add-imperfections">Add Natural Imperfections</Label>
                <Switch
                  id="add-imperfections"
                  checked={config.add_imperfections}
                  onCheckedChange={(checked) => setConfig({ ...config, add_imperfections: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="vary-quality">Vary Quality</Label>
                <Switch
                  id="vary-quality"
                  checked={config.vary_quality}
                  onCheckedChange={(checked) => setConfig({ ...config, vary_quality: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="remove-ai-signatures">Remove AI Signatures</Label>
                <Switch
                  id="remove-ai-signatures"
                  checked={config.remove_ai_signatures}
                  onCheckedChange={(checked) => setConfig({ ...config, remove_ai_signatures: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="add-realistic-noise">Add Realistic Noise</Label>
                <Switch
                  id="add-realistic-noise"
                  checked={config.add_realistic_noise}
                  onCheckedChange={(checked) => setConfig({ ...config, add_realistic_noise: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="normalize-colors">Normalize Colors</Label>
                <Switch
                  id="normalize-colors"
                  checked={config.normalize_colors}
                  onCheckedChange={(checked) => setConfig({ ...config, normalize_colors: checked })}
                />
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleProcess}
                disabled={!file || isProcessing}
                className="flex-1"
              >
                <Upload className="mr-2 h-4 w-4" />
                Process
              </Button>
              <Button
                onClick={handleTest}
                disabled={!file || isProcessing}
                variant="outline"
                className="flex-1"
              >
                <TestTube className="mr-2 h-4 w-4" />
                Test Detection
              </Button>
            </div>
          </CardContent>
        </Card>

        {testResults && (
          <Card>
            <CardHeader>
              <CardTitle>Detection Test Results</CardTitle>
              <CardDescription>
                Results from AI detection tools
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">Average Score</span>
                  <span className={testResults.average_score < 0.3 ? 'text-green-600' : 'text-red-600'}>
                    {(testResults.average_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className={`p-3 rounded-lg ${testResults.passed ? 'bg-green-50 dark:bg-green-950' : 'bg-red-50 dark:bg-red-950'}`}>
                  <div className="font-semibold">
                    {testResults.passed ? '✅ Passed' : '❌ Failed'}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Lower score = better (more undetectable)
                  </div>
                </div>
              </div>

              {testResults.tests && (
                <div className="space-y-2">
                  <div className="font-semibold">Individual Tests</div>
                  {Object.entries(testResults.tests).map(([tool, result]: [string, any]) => (
                    <div key={tool} className="p-2 bg-muted rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize">{tool}</span>
                        <span className={result.passed ? 'text-green-600' : 'text-red-600'}>
                          {(result.score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
