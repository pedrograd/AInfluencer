'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { Image, Video, Library, Users, Sparkles, CheckCircle2, XCircle } from 'lucide-react'
import { comfyUI } from '@/lib/api/comfyui'
import { cn } from '@/lib/utils/cn'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/Tooltip'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Dashboard() {
  const [systemStatus, setSystemStatus] = useState<{
    connected: boolean
    loading: boolean
  }>({ connected: false, loading: true })
  const [stats, setStats] = useState<{
    totalImages: number
    totalVideos: number
    totalCharacters: number
    loading: boolean
  }>({ totalImages: 0, totalVideos: 0, totalCharacters: 0, loading: true })

  useEffect(() => {
    checkSystemStatus()
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/stats`)
      const data = await response.json()
      if (data.success) {
        setStats({
          totalImages: data.data.total_images || 0,
          totalVideos: data.data.total_videos || 0,
          totalCharacters: data.data.total_characters || 0,
          loading: false,
        })
      }
    } catch (error) {
      console.error('Failed to load stats:', error)
      setStats(prev => ({ ...prev, loading: false }))
    }
  }

  const checkSystemStatus = async () => {
    try {
      await comfyUI.getSystemStats()
      setSystemStatus({ connected: true, loading: false })
    } catch (error) {
      console.error('ComfyUI connection error:', error)
      setSystemStatus({ connected: false, loading: false })
    }
  }

  const handleRetryConnection = () => {
    setSystemStatus({ connected: false, loading: true })
    checkSystemStatus()
  }

  const quickActions = [
    {
      title: 'Generate Image',
      description: 'Create ultra-realistic images',
      href: '/generate/image',
      icon: Image,
      color: 'text-blue-500',
    },
    {
      title: 'Generate Video',
      description: 'Create ultra-realistic videos',
      href: '/generate/video',
      icon: Video,
      color: 'text-purple-500',
    },
    {
      title: 'Media Library',
      description: 'Browse all your media',
      href: '/library',
      icon: Library,
      color: 'text-green-500',
    },
    {
      title: 'Characters',
      description: 'Manage your characters',
      href: '/characters',
      icon: Users,
      color: 'text-orange-500',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Ultra-Realistic AI Media Generator
        </p>
      </div>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5" />
            <span>System Status</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {systemStatus.loading ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              ) : systemStatus.connected ? (
                <>
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <span className="text-sm">ComfyUI Connected</span>
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span className="text-sm">ComfyUI Disconnected</span>
                </>
              )}
            </div>
            {!systemStatus.connected && !systemStatus.loading && (
              <Button size="sm" variant="outline" onClick={handleRetryConnection}>
                Retry
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight mb-4">Quick Actions</h2>
        <TooltipProvider>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {quickActions.map((action) => {
              const Icon = action.icon
              return (
                <Tooltip key={action.href} delayDuration={200}>
                  <TooltipTrigger asChild>
                    <Card className="hover:shadow-lg transition-shadow">
                      <CardHeader>
                        <div className="flex items-center space-x-2">
                          <Icon className={cn('h-6 w-6', action.color)} />
                          <CardTitle className="text-lg">{action.title}</CardTitle>
                        </div>
                        <CardDescription>{action.description}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Button asChild className="w-full">
                          <Link href={action.href}>Go to {action.title}</Link>
                        </Button>
                      </CardContent>
                    </Card>
                  </TooltipTrigger>
                  <TooltipContent side="top">
                    <p className="max-w-xs text-sm">{action.description}</p>
                  </TooltipContent>
                </Tooltip>
              )
            })}
          </div>
        </TooltipProvider>
      </div>

      {/* Statistics */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Images</CardTitle>
            <Image className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.loading ? '...' : stats.totalImages.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">AI generated images</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Videos</CardTitle>
            <Video className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.loading ? '...' : stats.totalVideos.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">AI generated videos</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Characters</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.loading ? '...' : stats.totalCharacters.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">Active characters</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
