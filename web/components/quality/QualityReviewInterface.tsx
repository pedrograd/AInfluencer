'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { backendAPI } from '@/lib/api/backend'
import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react'

interface QualityReviewInterfaceProps {
  mediaId: string
  onReviewComplete?: () => void
}

export function QualityReviewInterface({ mediaId, onReviewComplete }: QualityReviewInterfaceProps) {
  const [reviewerId, setReviewerId] = useState('')
  const [decision, setDecision] = useState<'approve' | 'reject' | 'improve'>('approve')
  const [qualityScore, setQualityScore] = useState(8.0)
  const [faceScore, setFaceScore] = useState(8.0)
  const [technicalScore, setTechnicalScore] = useState(8.0)
  const [realismScore, setRealismScore] = useState(8.0)
  const [notes, setNotes] = useState('')
  const [checklistScores, setChecklistScores] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!reviewerId.trim()) {
      alert('Please enter reviewer ID')
      return
    }

    setLoading(true)
    try {
      const response = await backendAPI.createQualityReview({
        media_id: mediaId,
        reviewer_id: reviewerId,
        decision,
        quality_score: qualityScore,
        face_score: faceScore,
        technical_score: technicalScore,
        realism_score: realismScore,
        notes,
        checklist_scores: checklistScores,
      })

      if (response.success) {
        alert(`Review ${decision}d successfully!`)
        if (onReviewComplete) {
          onReviewComplete()
        }
      } else {
        alert('Failed to submit review')
      }
    } catch (error: any) {
      alert(error.message || 'Failed to submit review')
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async () => {
    if (!reviewerId.trim()) {
      alert('Please enter reviewer ID')
      return
    }

    setLoading(true)
    try {
      const response = await backendAPI.rejectContent({
        media_id: mediaId,
        rejection_reason: 'quality',
        quality_score: qualityScore,
        details: {
          face_score: faceScore,
          technical_score: technicalScore,
          realism_score: realismScore,
          notes,
        },
      })

      if (response.success) {
        alert('Content rejected and logged')
        if (onReviewComplete) {
          onReviewComplete()
        }
      } else {
        alert('Failed to reject content')
      }
    } catch (error: any) {
      alert(error.message || 'Failed to reject content')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quality Review</CardTitle>
        <CardDescription>Manual review for media ID: {mediaId}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="reviewer">Reviewer ID</Label>
          <Input
            id="reviewer"
            value={reviewerId}
            onChange={(e) => setReviewerId(e.target.value)}
            placeholder="Enter reviewer identifier"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="decision">Decision</Label>
          <Select value={decision} onValueChange={(v: any) => setDecision(v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="approve">Approve</SelectItem>
              <SelectItem value="reject">Reject</SelectItem>
              <SelectItem value="improve">Needs Improvement</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Overall Quality: {qualityScore.toFixed(1)}/10</Label>
            <input
              type="range"
              min="0"
              max="10"
              step="0.1"
              value={qualityScore}
              onChange={(e) => setQualityScore(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <Label>Face Quality: {faceScore.toFixed(1)}/10</Label>
            <input
              type="range"
              min="0"
              max="10"
              step="0.1"
              value={faceScore}
              onChange={(e) => setFaceScore(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <Label>Technical Quality: {technicalScore.toFixed(1)}/10</Label>
            <input
              type="range"
              min="0"
              max="10"
              step="0.1"
              value={technicalScore}
              onChange={(e) => setTechnicalScore(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <Label>Realism Score: {realismScore.toFixed(1)}/10</Label>
            <input
              type="range"
              min="0"
              max="10"
              step="0.1"
              value={realismScore}
              onChange={(e) => setRealismScore(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="notes">Notes</Label>
          <Textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Additional notes about the review..."
            rows={4}
          />
        </div>

        <div className="flex gap-2">
          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="flex-1"
            variant={decision === 'approve' ? 'default' : 'outline'}
          >
            <CheckCircle2 className="mr-2 h-4 w-4" />
            Submit Review
          </Button>
          {decision === 'reject' && (
            <Button
              onClick={handleReject}
              disabled={loading}
              variant="destructive"
              className="flex-1"
            >
              <XCircle className="mr-2 h-4 w-4" />
              Reject & Log
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
