'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { History, Search, Star, Trash2 } from 'lucide-react'

interface PromptHistoryItem {
  id: string
  prompt: string
  timestamp: string
  favorite: boolean
}

interface PromptHistoryProps {
  onPromptSelected?: (prompt: string) => void
}

export function PromptHistory({ onPromptSelected }: PromptHistoryProps) {
  const [history, setHistory] = useState<PromptHistoryItem[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)

  useEffect(() => {
    // Load from localStorage
    const saved = localStorage.getItem('prompt_history')
    if (saved) {
      try {
        setHistory(JSON.parse(saved))
      } catch (e) {
        console.error('Failed to load prompt history:', e)
      }
    }
  }, [])

  const filteredHistory = history.filter(item => {
    const matchesSearch = item.prompt.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFavorite = !showFavoritesOnly || item.favorite
    return matchesSearch && matchesFavorite
  })

  const toggleFavorite = (id: string) => {
    const updated = history.map(item =>
      item.id === id ? { ...item, favorite: !item.favorite } : item
    )
    setHistory(updated)
    localStorage.setItem('prompt_history', JSON.stringify(updated))
  }

  const deleteItem = (id: string) => {
    const updated = history.filter(item => item.id !== id)
    setHistory(updated)
    localStorage.setItem('prompt_history', JSON.stringify(updated))
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <History className="h-5 w-5" />
          <span>Prompt History</span>
        </CardTitle>
        <CardDescription>
          View and reuse your previous prompts
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search prompts..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="favorites-only"
            checked={showFavoritesOnly}
            onChange={(e) => setShowFavoritesOnly(e.target.checked)}
            className="rounded"
          />
          <label htmlFor="favorites-only" className="text-sm cursor-pointer">
            Show favorites only
          </label>
        </div>

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {filteredHistory.length > 0 ? (
            filteredHistory.map((item) => (
              <div
                key={item.id}
                className="p-3 border rounded-md hover:bg-secondary transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <p className="text-sm">{item.prompt}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(item.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onPromptSelected?.(item.prompt)}
                    >
                      Use
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleFavorite(item.id)}
                    >
                      <Star
                        className={`h-4 w-4 ${
                          item.favorite ? 'fill-yellow-400 text-yellow-400' : ''
                        }`}
                      />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteItem(item.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              No prompts in history yet
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
