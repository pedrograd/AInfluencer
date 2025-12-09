'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Image, Video, Search, Filter, Grid, List, Download, Trash2, Shield, Tag, FolderPlus, ArrowUpDown, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import { backendAPI } from '@/lib/api/backend'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface MediaItem {
  id: string
  type: 'image' | 'video'
  source: 'ai_generated' | 'personal'
  file_name: string
  file_size: number
  width?: number
  height?: number
  thumbnail_path?: string
  character_id?: string
  character_name?: string
  tags: string[]
  created_at: string
  quality_score?: number
}

export default function MediaLibraryPage() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<'image' | 'video' | 'all'>('all')
  const [sourceFilter, setSourceFilter] = useState<'ai_generated' | 'personal' | 'all'>('all')
  const [dateFilter, setDateFilter] = useState<'all' | 'today' | 'week' | 'month'>('all')
  const [qualityFilter, setQualityFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all')
  const [characterFilter, setCharacterFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'created_at' | 'quality' | 'size' | 'name'>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [media, setMedia] = useState<MediaItem[]>([])
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  const [characters, setCharacters] = useState<Array<{ id: string; name: string }>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    loadMedia()
    loadCharacters()
  }, [typeFilter, sourceFilter, dateFilter, qualityFilter, characterFilter, sortBy, sortOrder, page])

  const loadCharacters = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/characters?limit=100`)
      const data = await response.json()
      if (data.success) {
        setCharacters((data.data.characters || []).map((c: any) => ({ id: c.id, name: c.name })))
      }
    } catch (error) {
      console.error('Failed to load characters:', error)
    }
  }

  const loadMedia = async () => {
    try {
      setIsLoading(true)
      
      // Build query params
      const params = new URLSearchParams()
      if (typeFilter !== 'all') params.append('type', typeFilter)
      if (sourceFilter !== 'all') params.append('source', sourceFilter)
      if (characterFilter !== 'all') params.append('character_id', characterFilter)
      params.append('page', page.toString())
      params.append('limit', '50')
      params.append('sort', sortBy)
      params.append('order', sortOrder)

      // Apply date filter
      if (dateFilter !== 'all') {
        const now = new Date()
        let startDate: Date
        if (dateFilter === 'today') {
          startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
        } else if (dateFilter === 'week') {
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        } else if (dateFilter === 'month') {
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        } else {
          startDate = new Date(0)
        }
        // Note: Backend should handle date filtering, but we'll filter client-side for now
      }

      const response = await fetch(`${API_BASE}/api/media?${params.toString()}`)
      const data = await response.json()
      
      if (data.success) {
        let items = data.data.items || []
        
        // Apply client-side filters (date, quality, search)
        if (dateFilter !== 'all') {
          const now = new Date()
          let startDate: Date
          if (dateFilter === 'today') {
            startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
          } else if (dateFilter === 'week') {
            startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
          } else {
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
          }
          items = items.filter((item: MediaItem) => new Date(item.created_at) >= startDate)
        }

        if (qualityFilter !== 'all') {
          items = items.filter((item: MediaItem) => {
            const score = item.quality_score || 0
            if (qualityFilter === 'high') return score >= 8
            if (qualityFilter === 'medium') return score >= 5 && score < 8
            return score < 5
          })
        }

        if (searchQuery) {
          const query = searchQuery.toLowerCase()
          items = items.filter((item: MediaItem) =>
            item.file_name.toLowerCase().includes(query) ||
            item.tags.some(tag => tag.toLowerCase().includes(query)) ||
            item.character_name?.toLowerCase().includes(query)
          )
        }

        setMedia(items)
        setTotal(data.data.total || 0)
        setTotalPages(data.data.total_pages || 1)
      }
    } catch (error) {
      console.error('Failed to load media:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this media item?')) return

    try {
      const response = await fetch(`${API_BASE}/api/media/${id}`, {
        method: 'DELETE',
      })
      const data = await response.json()
      if (data.success) {
        await loadMedia()
        setSelectedItems(new Set())
      }
    } catch (error) {
      console.error('Failed to delete media:', error)
      alert('Failed to delete media')
    }
  }

  const handleBulkDelete = async () => {
    if (selectedItems.size === 0) return
    if (!confirm(`Are you sure you want to delete ${selectedItems.size} items?`)) return

    try {
      const deletePromises = Array.from(selectedItems).map(id =>
        fetch(`${API_BASE}/api/media/${id}`, { method: 'DELETE' })
      )
      await Promise.all(deletePromises)
      await loadMedia()
      setSelectedItems(new Set())
    } catch (error) {
      console.error('Failed to delete media:', error)
      alert('Failed to delete some media items')
    }
  }

  const handleBulkDownload = async () => {
    if (selectedItems.size === 0) return
    
    // Download each item individually
    selectedItems.forEach(id => {
      window.open(`${API_BASE}/api/media/${id}/download`, '_blank')
    })
  }

  const handleDownload = (id: string) => {
    window.open(`${API_BASE}/api/media/${id}/download`, '_blank')
  }

  const toggleSelect = (id: string) => {
    const newSelected = new Set(selectedItems)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedItems(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedItems.size === media.length) {
      setSelectedItems(new Set())
    } else {
      setSelectedItems(new Set(media.map(item => item.id)))
    }
  }

  const clearFilters = () => {
    setSearchQuery('')
    setTypeFilter('all')
    setSourceFilter('all')
    setDateFilter('all')
    setQualityFilter('all')
    setCharacterFilter('all')
    setSortBy('created_at')
    setSortOrder('desc')
    setPage(1)
  }

  const getMediaUrl = (item: MediaItem) => {
    if (item.thumbnail_path) {
      return `${API_BASE}/api/media/${item.id}/download`
    }
    return `${API_BASE}/api/media/${item.id}/download`
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Media Library</h1>
          <p className="text-muted-foreground">
            Browse and manage all your media ({total} items)
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={loadMedia}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button
            variant={viewMode === 'grid' ? 'default' : 'outline'}
            size="icon"
            onClick={() => setViewMode('grid')}
          >
            <Grid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'outline'}
            size="icon"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedItems.size > 0 && (
        <Card className="bg-primary/10 border-primary/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {selectedItems.size} item{selectedItems.size !== 1 ? 's' : ''} selected
              </span>
              <div className="flex items-center space-x-2">
                <Button size="sm" variant="outline" onClick={handleBulkDownload}>
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
                <Button size="sm" variant="destructive" onClick={handleBulkDelete}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </Button>
                <Button size="sm" variant="outline" onClick={() => setSelectedItems(new Set())}>
                  Clear Selection
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Filter className="h-5 w-5" />
            <span>Filters & Search</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by filename, tags, or character..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
              <Select value={typeFilter} onValueChange={(value) => { setTypeFilter(value as any); setPage(1) }}>
                <SelectTrigger>
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="image">Images</SelectItem>
                  <SelectItem value="video">Videos</SelectItem>
                </SelectContent>
              </Select>
              <Select value={sourceFilter} onValueChange={(value) => { setSourceFilter(value as any); setPage(1) }}>
                <SelectTrigger>
                  <SelectValue placeholder="Source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sources</SelectItem>
                  <SelectItem value="ai_generated">AI Generated</SelectItem>
                  <SelectItem value="personal">Personal</SelectItem>
                </SelectContent>
              </Select>
              <Select value={dateFilter} onValueChange={(value) => { setDateFilter(value as any); setPage(1) }}>
                <SelectTrigger>
                  <SelectValue placeholder="Date" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Time</SelectItem>
                  <SelectItem value="today">Today</SelectItem>
                  <SelectItem value="week">This Week</SelectItem>
                  <SelectItem value="month">This Month</SelectItem>
                </SelectContent>
              </Select>
              <Select value={qualityFilter} onValueChange={(value) => { setQualityFilter(value as any); setPage(1) }}>
                <SelectTrigger>
                  <SelectValue placeholder="Quality" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Quality</SelectItem>
                  <SelectItem value="high">High (8+)</SelectItem>
                  <SelectItem value="medium">Medium (5-7)</SelectItem>
                  <SelectItem value="low">Low (&lt;5)</SelectItem>
                </SelectContent>
              </Select>
              <Select value={characterFilter} onValueChange={(value) => { setCharacterFilter(value); setPage(1) }}>
                <SelectTrigger>
                  <SelectValue placeholder="Character" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Characters</SelectItem>
                  {characters.map(char => (
                    <SelectItem key={char.id} value={char.id}>{char.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={`${sortBy}-${sortOrder}`} onValueChange={(value) => {
                const [sort, order] = value.split('-')
                setSortBy(sort as any)
                setSortOrder(order as any)
                setPage(1)
              }}>
                <SelectTrigger>
                  <SelectValue placeholder="Sort" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="created_at-desc">Newest First</SelectItem>
                  <SelectItem value="created_at-asc">Oldest First</SelectItem>
                  <SelectItem value="quality-desc">Highest Quality</SelectItem>
                  <SelectItem value="quality-asc">Lowest Quality</SelectItem>
                  <SelectItem value="size-desc">Largest First</SelectItem>
                  <SelectItem value="size-asc">Smallest First</SelectItem>
                  <SelectItem value="name-asc">Name A-Z</SelectItem>
                  <SelectItem value="name-desc">Name Z-A</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" onClick={clearFilters}>
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Media Grid/List */}
      {isLoading ? (
        <Card>
          <CardContent className="flex items-center justify-center min-h-[400px]">
            <div className="text-center text-muted-foreground">
              <RefreshCw className="h-12 w-12 mx-auto mb-4 opacity-50 animate-spin" />
              <p>Loading media...</p>
            </div>
          </CardContent>
        </Card>
      ) : media.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center min-h-[400px]">
            <div className="text-center text-muted-foreground">
              <Image className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No media found</p>
              <p className="text-sm mt-2">Upload or generate media to get started</p>
            </div>
          </CardContent>
        </Card>
      ) : viewMode === 'grid' ? (
        <>
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
            {media.map((item) => (
              <Card key={item.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                <div className="relative aspect-square w-full overflow-hidden">
                  <Checkbox
                    checked={selectedItems.has(item.id)}
                    onCheckedChange={() => toggleSelect(item.id)}
                    className="absolute top-2 left-2 z-10 bg-background/80"
                  />
                  {item.type === 'image' ? (
                    <img
                      src={getMediaUrl(item)}
                      alt={item.file_name}
                      className="h-full w-full object-cover"
                      onError={(e) => {
                        e.currentTarget.src = '/placeholder-image.png'
                      }}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full bg-muted">
                      <Video className="h-12 w-12 text-muted-foreground" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-black/0 hover:bg-black/50 transition-colors flex items-center justify-center opacity-0 hover:opacity-100">
                    <div className="flex space-x-2">
                      <Link href={`/anti-detection?media_id=${item.id}`}>
                        <Button size="icon" variant="secondary" title="Test Detection">
                          <Shield className="h-4 w-4" />
                        </Button>
                      </Link>
                      <Button size="icon" variant="secondary" onClick={() => handleDownload(item.id)} title="Download">
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button size="icon" variant="destructive" onClick={() => handleDelete(item.id)} title="Delete">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  {item.quality_score !== undefined && (
                    <div className="absolute top-2 right-2 bg-background/80 px-2 py-1 rounded text-xs font-medium">
                      {item.quality_score.toFixed(1)}
                    </div>
                  )}
                </div>
                <CardContent className="p-3">
                  <p className="text-sm font-medium truncate">{item.file_name}</p>
                  <div className="flex items-center justify-between mt-1">
                    <p className="text-xs text-muted-foreground">
                      {(item.file_size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    {item.character_name && (
                      <p className="text-xs text-muted-foreground truncate ml-2">
                        {item.character_name}
                      </p>
                    )}
                  </div>
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {item.tags.slice(0, 3).map((tag, idx) => (
                        <span key={idx} className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-center space-x-2">
              <Button variant="outline" disabled={page === 1} onClick={() => setPage(p => Math.max(1, p - 1))}>
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button variant="outline" disabled={page >= totalPages} onClick={() => setPage(p => Math.min(totalPages, p + 1))}>
                Next
              </Button>
            </div>
          )}
        </>
      ) : (
        <>
          <div className="space-y-2">
            <div className="flex items-center space-x-2 p-2 border-b">
              <Checkbox
                checked={selectedItems.size === media.length && media.length > 0}
                onCheckedChange={toggleSelectAll}
              />
              <span className="text-sm font-medium flex-1">Select All</span>
            </div>
            {media.map((item) => (
              <Card key={item.id}>
                <CardContent className="flex items-center space-x-4 p-4">
                  <Checkbox
                    checked={selectedItems.has(item.id)}
                    onCheckedChange={() => toggleSelect(item.id)}
                  />
                  <div className="relative h-16 w-16 flex-shrink-0 overflow-hidden rounded">
                    {item.type === 'image' ? (
                      <img
                        src={getMediaUrl(item)}
                        alt={item.file_name}
                        className="h-full w-full object-cover"
                        onError={(e) => {
                          e.currentTarget.src = '/placeholder-image.png'
                        }}
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full bg-muted">
                        <Video className="h-6 w-6 text-muted-foreground" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{item.file_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {item.type} • {(item.file_size / 1024 / 1024).toFixed(2)} MB • {new Date(item.created_at).toLocaleDateString()}
                      {item.character_name && ` • ${item.character_name}`}
                      {item.quality_score !== undefined && ` • Quality: ${item.quality_score.toFixed(1)}`}
                    </p>
                    {item.tags && item.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {item.tags.map((tag, idx) => (
                          <span key={idx} className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Link href={`/anti-detection?media_id=${item.id}`}>
                      <Button size="icon" variant="outline" title="Test Detection">
                        <Shield className="h-4 w-4" />
                      </Button>
                    </Link>
                    <Button size="icon" variant="outline" onClick={() => handleDownload(item.id)} title="Download">
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button size="icon" variant="destructive" onClick={() => handleDelete(item.id)} title="Delete">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-center space-x-2">
              <Button variant="outline" disabled={page === 1} onClick={() => setPage(p => Math.max(1, p - 1))}>
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button variant="outline" disabled={page >= totalPages} onClick={() => setPage(p => Math.min(totalPages, p + 1))}>
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
