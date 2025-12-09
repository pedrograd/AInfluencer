/**
 * WebSocket hook for real-time generation updates
 */
import { useEffect, useRef, useState, useCallback } from 'react'

export interface JobUpdate {
  type: 'job_update' | 'batch_update'
  job_id?: string
  batch_job_id?: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'error'
  progress: number
  message?: string
  media_id?: string
  error?: string
  timestamp: string
}

export function useWebSocket(jobId?: string, batchJobId?: string) {
  const [update, setUpdate] = useState<JobUpdate | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  const connect = useCallback(() => {
    if (!jobId && !batchJobId) return

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    const ws = new WebSocket('ws://localhost:8000/ws')
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      console.log('WebSocket connected')

      // Subscribe to job updates
      if (jobId) {
        ws.send(JSON.stringify({
          type: 'subscribe',
          job_id: jobId
        }))
      } else if (batchJobId) {
        ws.send(JSON.stringify({
          type: 'subscribe_batch',
          batch_job_id: batchJobId
        }))
      }
    }

    ws.onmessage = (event) => {
      try {
        const data: JobUpdate = JSON.parse(event.data)
        setUpdate(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }

    ws.onclose = () => {
      setConnected(false)
      console.log('WebSocket disconnected')

      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        if (jobId || batchJobId) {
          connect()
        }
      }, 3000)
    }
  }, [jobId, batchJobId])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (wsRef.current) {
      if (jobId) {
        wsRef.current.send(JSON.stringify({
          type: 'unsubscribe',
          job_id: jobId
        }))
      } else if (batchJobId) {
        wsRef.current.send(JSON.stringify({
          type: 'unsubscribe',
          batch_job_id: batchJobId
        }))
      }
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
  }, [jobId, batchJobId])

  useEffect(() => {
    if (jobId || batchJobId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [jobId, batchJobId, connect, disconnect])

  return {
    update,
    connected,
    reconnect: connect,
    disconnect
  }
}
