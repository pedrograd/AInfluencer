'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, Tag, Star, Heart, MessageSquare, Search } from 'lucide-react'

export function MediaLibraryFeatures() {
  const [mediaId, setMediaId] = useState('')
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAutoTag = async () => {
    if (!mediaId) {
      setError('Please provide a media ID')
      return
    }

    setProcessing(true)
    setError(null)
    setResult(null)

    try {
      const response = await backendAPI.autoTagMedia(mediaId)
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const errorMessage = (response as any)?.error?.message
      if (success) {
        setResult({ type: 'tags', data })
      } else {
        setError(errorMessage || 'Auto-tagging failed')
      }
    } catch (err: any) {
      setError(err.message || 'Auto-tagging failed')
    } finally {
      setProcessing(false)
    }
  }

  const handleRecognizeFaces = async () => {
    if (!mediaId) {
      setError('Please provide a media ID')
      return
    }

    setProcessing(true)
    setError(null)
    setResult(null)

    try {
      const response = await backendAPI.recognizeFaces(mediaId)
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const errorMessage = (response as any)?.error?.message
      if (success) {
        setResult({ type: 'faces', data })
      } else {
        setError(errorMessage || 'Face recognition failed')
      }
    } catch (err: any) {
      setError(err.message || 'Face recognition failed')
    } finally {
      setProcessing(false)
    }
  }

  const handleAddFavorite = async () => {
    if (!mediaId) {
      setError('Please provide a media ID')
      return
    }

    setProcessing(true)
    setError(null)

    try {
      const response = await backendAPI.addFavorite(mediaId)
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const errorMessage = (response as any)?.error?.message
      if (success) {
        setResult({ type: 'favorite', data })
      } else {
        setError(errorMessage || 'Failed to add favorite')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to add favorite')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Media Library Features</CardTitle>
        <CardDescription>
          Auto-tagging, face recognition, favorites, ratings, and more
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Media ID</label>
          <Input
            value={mediaId}
            onChange={(e) => setMediaId(e.target.value)}
            placeholder="Enter media ID"
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <Button
            onClick={handleAutoTag}
            disabled={processing || !mediaId}
            variant="outline"
            size="sm"
          >
            <Tag className="mr-2 h-4 w-4" />
            Auto-Tag
          </Button>

          <Button
            onClick={handleRecognizeFaces}
            disabled={processing || !mediaId}
            variant="outline"
            size="sm"
          >
            <Search className="mr-2 h-4 w-4" />
            Recognize Faces
          </Button>

          <Button
            onClick={handleAddFavorite}
            disabled={processing || !mediaId}
            variant="outline"
            size="sm"
          >
            <Heart className="mr-2 h-4 w-4" />
            Add Favorite
          </Button>
        </div>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-sm text-red-800 dark:text-red-200">
            {error}
          </div>
        )}

        {result && (
          <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
            <p className="text-sm text-green-800 dark:text-green-200">
              {result.type === 'tags' && `Tags: ${result.data.tags?.join(', ') || 'None'}`}
              {result.type === 'faces' && `Faces detected: ${result.data.faces_detected || 0}`}
              {result.type === 'favorite' && 'Added to favorites!'}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
