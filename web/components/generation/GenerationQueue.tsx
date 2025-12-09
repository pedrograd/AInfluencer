'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { backend } from '@/lib/api/backend'
import { Loader2, Play, Pause, Trash2, ArrowUp, ArrowDown } from 'lucide-react'

interface QueueItem {
  id: string
  prompt: string
  status: 'pending' | 'queued' | 'processing' | 'completed' | 'failed'
  priority: 'low' | 'normal' | 'high' | 'urgent'
  created_at: string
  progress?: number
}

export function GenerationQueue() {
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [loading, setLoading] = useState(false)

  const loadQueue = async () => {
    setLoading(true)
    try {
      const { data } = await backend.get('/api/generation/queue')
      const success = data?.success ?? true
      const jobs = data?.data?.jobs ?? data?.jobs ?? []

      if (success) {
        setQueue(jobs)
      }
    } catch (err) {
      console.error('Load queue error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadQueue()
    const interval = setInterval(loadQueue, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const changePriority = async (jobId: string, newPriority: string) => {
    try {
      await backend.put(`/api/generation/jobs/${jobId}/priority`, { priority: newPriority })
      loadQueue()
    } catch (err) {
      console.error('Change priority error:', err)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500'
      case 'high': return 'bg-orange-500'
      case 'normal': return 'bg-blue-500'
      case 'low': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-500'
      case 'processing': return 'text-blue-500'
      case 'failed': return 'text-red-500'
      case 'pending': return 'text-yellow-500'
      default: return 'text-gray-500'
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generation Queue</CardTitle>
        <CardDescription>
          Manage your generation queue and priorities
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-muted-foreground">
            {queue.length} job{queue.length !== 1 ? 's' : ''} in queue
          </span>
          <Button onClick={loadQueue} variant="outline" size="sm" disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Refresh'}
          </Button>
        </div>

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {queue.length > 0 ? (
            queue.map((item) => (
              <div
                key={item.id}
                className="p-3 border rounded-md hover:bg-secondary transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge className={getPriorityColor(item.priority)}>
                        {item.priority}
                      </Badge>
                      <span className={`text-xs font-medium ${getStatusColor(item.status)}`}>
                        {item.status}
                      </span>
                    </div>
                    <p className="text-sm line-clamp-2">{item.prompt}</p>
                    {item.progress !== undefined && (
                      <div className="mt-2">
                        <div className="w-full bg-secondary rounded-full h-1.5">
                          <div
                            className="bg-primary h-1.5 rounded-full transition-all"
                            style={{ width: `${item.progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(item.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex flex-col gap-1">
                    {item.priority !== 'urgent' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const priorities = ['low', 'normal', 'high', 'urgent']
                          const currentIndex = priorities.indexOf(item.priority)
                          if (currentIndex < priorities.length - 1) {
                            changePriority(item.id, priorities[currentIndex + 1])
                          }
                        }}
                      >
                        <ArrowUp className="h-3 w-3" />
                      </Button>
                    )}
                    {item.priority !== 'low' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const priorities = ['low', 'normal', 'high', 'urgent']
                          const currentIndex = priorities.indexOf(item.priority)
                          if (currentIndex > 0) {
                            changePriority(item.id, priorities[currentIndex - 1])
                          }
                        }}
                      >
                        <ArrowDown className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              Queue is empty
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
