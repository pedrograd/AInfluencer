'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { backendAPI } from '@/lib/api/backend'
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'

interface DashboardData {
  summary: {
    quality_avg: number
    approval_rate: number
    detection_avg: number
    generation_count: number
    pass_rate: number
    automation_rate: number
  }
  trends: {
    daily_metrics: Array<{
      date: string
      quality_avg: number
      approval_rate: number
      detection_avg: number
      generation_count: number
    }>
    trend: {
      quality: string
      approval: string
      detection: string
    }
  }
  alerts: Array<{
    type: string
    category: string
    message: string
    severity: string
  }>
}

export function QualityDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(7)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboard()
  }, [days])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await backendAPI.getQualityDashboard(days)
      if (response.success) {
        setData(response.data)
      } else {
        setError('Failed to load dashboard data')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto py-8">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!data) {
    return null
  }

  const { summary, trends, alerts } = data

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Quality Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive quality metrics and KPIs
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm">Period:</label>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-3 py-1 border rounded"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
          </select>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert, idx) => (
            <Alert
              key={idx}
              className={alert.severity === 'high' ? 'border-destructive/50 text-destructive' : ''}
            >
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>{alert.category.toUpperCase()}</AlertTitle>
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Quality Score</CardTitle>
            {trends.trend.quality === 'improving' ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : trends.trend.quality === 'declining' ? (
              <TrendingDown className="h-4 w-4 text-red-600" />
            ) : null}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.quality_avg.toFixed(1)}/10</div>
            <p className="text-xs text-muted-foreground">
              Target: ≥8.5
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approval Rate</CardTitle>
            {trends.trend.approval === 'improving' ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : trends.trend.approval === 'declining' ? (
              <TrendingDown className="h-4 w-4 text-red-600" />
            ) : null}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.approval_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Target: ≥80%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Detection Pass Rate</CardTitle>
            {trends.trend.detection === 'improving' ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : trends.trend.detection === 'declining' ? (
              <TrendingDown className="h-4 w-4 text-red-600" />
            ) : null}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.pass_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Target: ≥95%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Detection Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(summary.detection_avg * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Lower is better (Target: &lt;30%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Content Generated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.generation_count}</div>
            <p className="text-xs text-muted-foreground">
              Last {days} days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Automation Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.automation_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Target: ≥90%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Trends Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Quality Trends</CardTitle>
          <CardDescription>Daily metrics over the selected period</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {trends.daily_metrics.map((day, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 border rounded">
                <div className="text-sm font-medium">{day.date}</div>
                <div className="flex gap-4 text-sm">
                  <span>Quality: {day.quality_avg.toFixed(1)}</span>
                  <span>Approval: {day.approval_rate.toFixed(1)}%</span>
                  <span>Detection: {(day.detection_avg * 100).toFixed(1)}%</span>
                  <span>Count: {day.generation_count}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
