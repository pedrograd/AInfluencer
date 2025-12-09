'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { backendAPI } from '@/lib/api/backend'
import { Activity, AlertTriangle, CheckCircle2 } from 'lucide-react'

export function PerformanceMonitor() {
  const [metrics, setMetrics] = useState<any>(null)
  const [bottlenecks, setBottlenecks] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
    const interval = setInterval(loadMetrics, 5000) // Update every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const loadMetrics = async () => {
    try {
      // Get performance metrics
      const metricsResponse = await backendAPI.getSystemPerformanceMetrics()
      const metricsSuccess = (metricsResponse as any)?.success ?? true
      const metricsData = (metricsResponse as any)?.data ?? metricsResponse
      if (metricsSuccess) {
        setMetrics(metricsData)
      }

      // Get bottlenecks
      const bottlenecksResponse = await backendAPI.detectBottlenecks()
      const bottlenecksSuccess = (bottlenecksResponse as any)?.success ?? true
      const bottlenecksData = (bottlenecksResponse as any)?.data ?? bottlenecksResponse
      if (bottlenecksSuccess) {
        setBottlenecks(bottlenecksData)
      }
    } catch (error) {
      console.error('Failed to load performance metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !metrics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Monitor</CardTitle>
          <CardDescription>Loading performance metrics...</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>System Performance</span>
          </CardTitle>
          <CardDescription>Real-time system resource monitoring</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Memory Usage */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Memory Usage</span>
              <span className="font-medium">
                {metrics.memory.used_gb.toFixed(1)} GB / {metrics.memory.total_gb.toFixed(1)} GB
                ({metrics.memory.percent}%)
              </span>
            </div>
            <Progress
              value={metrics.memory.percent}
              className={`h-2 ${
                metrics.memory.percent > 90
                  ? 'bg-red-500'
                  : metrics.memory.percent > 80
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
            />
          </div>

          {/* CPU Usage */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>CPU Usage</span>
              <span className="font-medium">{metrics.cpu_percent.toFixed(1)}%</span>
            </div>
            <Progress
              value={metrics.cpu_percent}
              className={`h-2 ${
                metrics.cpu_percent > 90
                  ? 'bg-red-500'
                  : metrics.cpu_percent > 80
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
            />
          </div>

          {/* Disk Usage */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Disk Usage</span>
              <span className="font-medium">
                {metrics.disk.used_gb.toFixed(1)} GB / {metrics.disk.total_gb.toFixed(1)} GB
                ({metrics.disk.percent.toFixed(1)}%)
              </span>
            </div>
            <Progress
              value={metrics.disk.percent}
              className={`h-2 ${
                metrics.disk.percent > 90
                  ? 'bg-red-500'
                  : metrics.disk.percent > 80
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
            />
          </div>
        </CardContent>
      </Card>

      {/* Bottlenecks */}
      {bottlenecks && bottlenecks.bottlenecks && bottlenecks.bottlenecks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              <span>Performance Bottlenecks</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {bottlenecks.bottlenecks.map((bottleneck: any, idx: number) => (
                <div
                  key={idx}
                  className={`p-3 rounded-md border ${
                    bottleneck.severity === 'critical'
                      ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                      : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-medium text-sm">{bottleneck.type.toUpperCase()}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {bottleneck.message}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        💡 {bottleneck.recommendation}
                      </div>
                    </div>
                    <div
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        bottleneck.severity === 'critical'
                          ? 'bg-red-500 text-white'
                          : 'bg-yellow-500 text-white'
                      }`}
                    >
                      {bottleneck.severity}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {bottlenecks && bottlenecks.overall_status === 'ok' && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
              <CheckCircle2 className="h-5 w-5" />
              <span className="font-medium">All systems operating normally</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
