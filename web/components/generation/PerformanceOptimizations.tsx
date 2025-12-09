'use client'

import { memo, useMemo, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Zap } from 'lucide-react'

export interface PerformanceConfig {
  enable_caching: boolean
  batch_size: number
  parallel_processing: boolean
  lazy_loading: boolean
  image_optimization: boolean
  compression_level: 'low' | 'medium' | 'high'
}

interface PerformanceOptimizationsProps {
  config: PerformanceConfig
  onChange: (config: PerformanceConfig) => void
}

export const PerformanceOptimizations = memo(function PerformanceOptimizations({
  config,
  onChange,
}: PerformanceOptimizationsProps) {
  const updateConfig = useCallback((updates: Partial<PerformanceConfig>) => {
    onChange({ ...config, ...updates })
  }, [config, onChange])

  const compressionOptions = useMemo(() => [
    { value: 'low', label: 'Low (Fast, Larger Files)' },
    { value: 'medium', label: 'Medium (Balanced)' },
    { value: 'high', label: 'High (Slower, Smaller Files)' },
  ], [])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5" />
          Performance Optimizations
        </CardTitle>
        <CardDescription>
          Optimize generation and processing performance
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="enable-caching">Enable Caching</Label>
          <Switch
            id="enable-caching"
            checked={config.enable_caching}
            onCheckedChange={(checked) => updateConfig({ enable_caching: checked })}
          />
        </div>

        <div className="space-y-2">
          <Label>Batch Size: {config.batch_size}</Label>
          <Select
            value={config.batch_size.toString()}
            onValueChange={(value) => updateConfig({ batch_size: parseInt(value) })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1 (Sequential)</SelectItem>
              <SelectItem value="2">2</SelectItem>
              <SelectItem value="4">4 (Recommended)</SelectItem>
              <SelectItem value="8">8 (High Memory)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center justify-between">
          <Label htmlFor="parallel-processing">Parallel Processing</Label>
          <Switch
            id="parallel-processing"
            checked={config.parallel_processing}
            onCheckedChange={(checked) => updateConfig({ parallel_processing: checked })}
          />
        </div>

        <div className="flex items-center justify-between">
          <Label htmlFor="lazy-loading">Lazy Loading</Label>
          <Switch
            id="lazy-loading"
            checked={config.lazy_loading}
            onCheckedChange={(checked) => updateConfig({ lazy_loading: checked })}
          />
        </div>

        <div className="flex items-center justify-between">
          <Label htmlFor="image-optimization">Image Optimization</Label>
          <Switch
            id="image-optimization"
            checked={config.image_optimization}
            onCheckedChange={(checked) => updateConfig({ image_optimization: checked })}
          />
        </div>

        <div className="space-y-2">
          <Label>Compression Level</Label>
          <Select
            value={config.compression_level}
            onValueChange={(value) => updateConfig({ compression_level: value as 'low' | 'medium' | 'high' })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {compressionOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  )
})
