'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import type { PracticeReport } from '@/types/best-practices'

interface BestPracticesDashboardProps {
  onValidate?: (report: PracticeReport) => void
}

export function BestPracticesDashboard({ onValidate }: BestPracticesDashboardProps) {
  const [report, setReport] = useState<PracticeReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const fetchReport = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/best-practices/report')
      const data = await response.json()
      if (data.success) {
        setReport(data.data)
        onValidate?.(data.data)
      }
    } catch (error) {
      console.error('Failed to fetch best practices report:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReport()
  }, [])

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-600'
    if (score >= 0.7) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 border-red-500 text-red-800'
      case 'high': return 'bg-orange-100 border-orange-500 text-orange-800'
      case 'medium': return 'bg-yellow-100 border-yellow-500 text-yellow-800'
      case 'low': return 'bg-blue-100 border-blue-500 text-blue-800'
      default: return 'bg-gray-100 border-gray-500 text-gray-800'
    }
  }

  if (loading) {
    return (
      <Card className="p-6">
        <div className="text-center">Loading best practices report...</div>
      </Card>
    )
  }

  if (!report) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <p className="text-gray-600 mb-4">No best practices data available</p>
          <Button onClick={fetchReport}>Generate Report</Button>
        </div>
      </Card>
    )
  }

  const totalChecks = report.metadata?.total_checks ?? report.checks?.length ?? 0
  const totalViolations = report.metadata?.total_violations ?? report.violations?.length ?? 0
  const criticalCount = report.metadata?.critical_count ?? report.violations?.filter(v => v.severity === 'critical').length ?? 0

  const filteredViolations = selectedCategory === 'all'
    ? report.violations
    : report.violations.filter(v => v.category === selectedCategory)

  return (
    <div className="space-y-6">
      {/* Overall Score */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Best Practices Report</h2>
          <Button onClick={fetchReport} variant="outline">Refresh</Button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className={`text-4xl font-bold ${getScoreColor(report.overall_score)}`}>
              {(report.overall_score * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-600">Overall Score</div>
          </div>
          
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-800">
              {totalChecks}
            </div>
            <div className="text-sm text-gray-600">Total Checks</div>
          </div>
          
          <div className="text-center">
            <div className="text-4xl font-bold text-red-600">
              {totalViolations}
            </div>
            <div className="text-sm text-gray-600">Violations</div>
          </div>
          
          <div className="text-center">
            <div className="text-4xl font-bold text-orange-600">
              {criticalCount}
            </div>
            <div className="text-sm text-gray-600">Critical Issues</div>
          </div>
        </div>

        {/* Category Scores */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(report.category_scores || {}).map(([category, score]) => (
            <div key={category} className="p-3 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 capitalize">{category}</div>
              <div className={`text-2xl font-bold ${getScoreColor(score)}`}>
                {(score * 100).toFixed(0)}%
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Violations */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold">Violations</h3>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1 border rounded"
          >
            <option value="all">All Categories</option>
            <option value="content">Content</option>
            <option value="technical">Technical</option>
            <option value="quality">Quality</option>
            <option value="security">Security</option>
            <option value="performance">Performance</option>
            <option value="workflow">Workflow</option>
          </select>
        </div>

        <div className="space-y-3">
          {filteredViolations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No violations found
            </div>
          ) : (
            filteredViolations.map((violation, index) => (
              <Alert
                key={index}
                className={`border-l-4 ${getSeverityColor(violation.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-semibold mb-1">{violation.practice}</div>
                    <div className="text-sm mb-2">{violation.description}</div>
                    <div className="text-xs text-gray-600">
                      <span className="font-semibold">Location:</span> {violation.location}
                    </div>
                    <div className="text-xs text-gray-700 mt-2">
                      <span className="font-semibold">Suggestion:</span> {violation.suggestion}
                    </div>
                  </div>
                  <div className="ml-4">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${getSeverityColor(violation.severity)}`}>
                      {violation.severity.toUpperCase()}
                    </span>
                  </div>
                </div>
              </Alert>
            ))
          )}
        </div>
      </Card>

      {/* Recommendations */}
      {report.recommendations && report.recommendations.length > 0 && (
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4">Recommendations</h3>
          <ul className="space-y-2">
            {report.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Checks Summary */}
      <Card className="p-6">
        <h3 className="text-xl font-bold mb-4">Practice Checks</h3>
        <div className="space-y-3">
          {report.checks?.map((check, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <span className={`w-3 h-3 rounded-full mr-3 ${check.passed ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="font-medium">{check.practice}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className={`text-sm font-semibold ${getScoreColor(check.score)}`}>
                  {(check.score * 100).toFixed(0)}%
                </span>
                <span className="text-xs text-gray-600">
                  {check.violations_count || 0} violations
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
