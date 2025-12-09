'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, Book, Video, HelpCircle, FileText } from 'lucide-react'

interface HelpArticle {
  id: string
  title: string
  category: string
  content: string
  tags: string[]
}

export function HelpCenter() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const categories = [
    { id: 'getting-started', name: 'Getting Started', icon: Book },
    { id: 'tutorials', name: 'Video Tutorials', icon: Video },
    { id: 'features', name: 'Features', icon: HelpCircle },
    { id: 'api', name: 'API Documentation', icon: FileText }
  ]

  const articles: HelpArticle[] = [
    {
      id: '1',
      title: 'How to Create Your First Character',
      category: 'getting-started',
      content: 'Learn how to create and configure your first AI character...',
      tags: ['character', 'setup', 'beginner']
    },
    {
      id: '2',
      title: 'Understanding Face Consistency',
      category: 'features',
      content: 'Face consistency ensures the same face across all generations...',
      tags: ['face', 'consistency', 'advanced']
    },
    {
      id: '3',
      title: 'Quality Assurance System',
      category: 'features',
      content: 'Our QA system automatically scores and filters generated content...',
      tags: ['quality', 'qa', 'automation']
    }
  ]

  const filteredArticles = articles.filter(article => {
    const matchesSearch = article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         article.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         article.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    const matchesCategory = !selectedCategory || article.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Help Center</h1>
        <p className="text-muted-foreground">
          Find answers and learn how to use AInfluencer
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Help Articles</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for help..."
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {categories.map((category) => {
          const Icon = category.icon
          return (
            <Card
              key={category.id}
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => setSelectedCategory(
                selectedCategory === category.id ? null : category.id
              )}
            >
              <CardContent className="p-6 text-center">
                <Icon className="h-8 w-8 mx-auto mb-2" />
                <p className="font-medium">{category.name}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">Articles</h2>
        {filteredArticles.length > 0 ? (
          <div className="space-y-4">
            {filteredArticles.map((article) => (
              <Card key={article.id}>
                <CardHeader>
                  <CardTitle className="text-lg">{article.title}</CardTitle>
                  <CardDescription>
                    {categories.find(c => c.id === article.category)?.name}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">{article.content}</p>
                  <div className="flex flex-wrap gap-2">
                    {article.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 text-xs bg-secondary rounded-md"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-6 text-center text-muted-foreground">
              No articles found. Try a different search term.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
