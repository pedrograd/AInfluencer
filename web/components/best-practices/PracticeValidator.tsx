'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import type { PracticeCheck, PracticeReport, PracticeViolation } from '@/types/best-practices'

interface PracticeValidatorProps {
  prompt?: string
  negativePrompt?: string
  onValidationComplete?: (report: PracticeReport) => void
}

export function PracticeValidator({ 
  prompt = '', 
  negativePrompt = '',
  onValidationComplete 
}: PracticeValidatorProps) {
  const [validating, setValidating] = useState(false)
  const [report, setReport] = useState<PracticeReport | null>(null)
  const [error, setError] = useState<string | null>(null)

  const validatePrompt = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt to validate')
      return
    }

    setValidating(true)
    setError(null)

    try {
      const response = await fetch('/api/best-practices/validate/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          negative_prompt: negativePrompt
        })
      })

      const data = await response.json()
      
      if (data.success) {
        // Convert single check to report format
        const check = data.data
        const violations = (check.violations || []) as PracticeViolation[]

        const normalizedCheck: PracticeCheck = {
          ...check,
          violations,
          violations_count: check.violations_count ?? violations.length,
          details: check.details || {},
        }

        const report: PracticeReport = {
          timestamp: new Date().toISOString(),
          overall_score: normalizedCheck.score,
          category_scores: { content: normalizedCheck.score },
          checks: [normalizedCheck],
          violations,
          recommendations: violations.map((v) => v.suggestion),
          metadata: {
            total_checks: 1,
            total_violations: violations.length,
            critical_count: violations.filter((v) => v.severity === 'critical').length,
            high_count: violations.filter((v) => v.severity === 'high').length,
          },
        }
        
        setReport(report)
        onValidationComplete?.(report)
      } else {
        setError(data.error?.message || 'Validation failed')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to validate prompt')
    } finally {
      setValidating(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-600'
    if (score >= 0.7) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Best Practices Validator</h3>
        <p className="text-sm text-gray-600">
          Validate your prompt against best practices for content creation
        </p>
      </div>

      {error && (
        <Alert className="mb-4 bg-red-50 border-red-200 text-red-800">
          {error}
        </Alert>
      )}

      <div className="mb-4">
        <Button 
          onClick={validatePrompt} 
          disabled={validating || !prompt.trim()}
          className="w-full"
        >
          {validating ? 'Validating...' : 'Validate Prompt'}
        </Button>
      </div>

      {report && (
        <div className="space-y-4 mt-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <span className="font-medium">Overall Score</span>
            <span className={`text-2xl font-bold ${getScoreColor(report.overall_score)}`}>
              {(report.overall_score * 100).toFixed(0)}%
            </span>
          </div>

          {report.checks && report.checks[0] && (
            <div>
              <div className="flex items-center mb-2">
                <span className={`w-3 h-3 rounded-full mr-2 ${report.checks[0].passed ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="font-medium">{report.checks[0].practice}</span>
              </div>
              
              {report.checks[0].violations && report.checks[0].violations.length > 0 && (
                <div className="mt-3 space-y-2">
                  <div className="text-sm font-semibold text-gray-700">Issues Found:</div>
                  {report.checks[0].violations.map((violation, index) => (
                    <Alert 
                      key={index}
                      className="bg-yellow-50 border-yellow-200 text-yellow-800"
                    >
                      <div className="text-sm">
                        <div className="font-semibold mb-1">{violation.practice}</div>
                        <div className="mb-1">{violation.description}</div>
                        <div className="text-xs text-gray-600">
                          <strong>Suggestion:</strong> {violation.suggestion}
                        </div>
                      </div>
                    </Alert>
                  ))}
                </div>
              )}

              {report.checks[0].passed && (
                <Alert className="bg-green-50 border-green-200 text-green-800 mt-3">
                  ✓ Prompt follows best practices!
                </Alert>
              )}
            </div>
          )}

          {report.recommendations && report.recommendations.length > 0 && (
            <div className="mt-4">
              <div className="text-sm font-semibold mb-2">Recommendations:</div>
              <ul className="space-y-1">
                {report.recommendations.map((rec, index) => (
                  <li key={index} className="text-sm text-gray-700 flex items-start">
                    <span className="text-blue-600 mr-2">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
