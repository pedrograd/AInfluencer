'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Users, Plus, Edit, Trash2, Image as ImageIcon, Download, Upload, FileText, Search } from 'lucide-react'
import { CharacterForm } from '@/components/characters/CharacterForm'
import type { Character, CharacterFormData, CharacterTemplate } from '@/types/character'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function CharactersPage() {
  const [characters, setCharacters] = useState<Character[]>([])
  const [templates, setTemplates] = useState<Record<string, CharacterTemplate>>({})
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingCharacter, setEditingCharacter] = useState<Character | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadCharacters()
    loadTemplates()
  }, [])

  const loadCharacters = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`${API_BASE}/api/characters?limit=100`)
      const data = await response.json()
      if (data.success) {
        // Map API response to frontend format
        const characters = (data.data.characters || []).map((char: any) => ({
          ...char,
          faceReferences: (char.face_references || []).map((fr: any) => ({
            id: fr.id,
            fileName: fr.file_name,
            filePath: fr.file_path,
            imageUrl: fr.file_path ? `${API_BASE}/api/characters/${char.id}/face-references/${fr.id}/image` : undefined,
            width: fr.width,
            height: fr.height,
            metadata: fr.metadata,
            uploadedAt: fr.created_at,
            isPrimary: false, // TODO: Add primary flag to backend
          })),
          persona: char.persona || {},
          appearance: char.appearance || {},
          style: char.style || {},
          contentPreferences: char.content_preferences || {},
          consistencyRules: char.consistency_rules || {},
          faceReferenceCount: char.face_reference_count,
          mediaCount: char.media_count,
        }))
        setCharacters(characters)
      }
    } catch (error) {
      console.error('Failed to load characters:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadTemplates = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/characters/templates`)
      const data = await response.json()
      if (data.success) {
        setTemplates(data.data || {})
      }
    } catch (error) {
      console.error('Failed to load templates:', error)
    }
  }

  const handleCreate = () => {
    setEditingCharacter(null)
    setIsDialogOpen(true)
  }

  const handleEdit = (character: Character) => {
    setEditingCharacter(character)
    setIsDialogOpen(true)
  }

  const handleSave = async (formData: CharacterFormData) => {
    try {
      const url = editingCharacter
        ? `${API_BASE}/api/characters/${editingCharacter.id}`
        : `${API_BASE}/api/characters`
      
      const method = editingCharacter ? 'PUT' : 'POST'
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      const data = await response.json()
      
      if (data.success) {
        await loadCharacters()
        setIsDialogOpen(false)
        setEditingCharacter(null)
      } else {
        alert('Failed to save character: ' + (data.error || 'Unknown error'))
      }
    } catch (error) {
      console.error('Failed to save character:', error)
      alert('Failed to save character')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this character?')) {
      return
    }

    try {
      const response = await fetch(`${API_BASE}/api/characters/${id}`, {
        method: 'DELETE',
      })

      const data = await response.json()
      
      if (data.success) {
        await loadCharacters()
      } else {
        alert('Failed to delete character')
      }
    } catch (error) {
      console.error('Failed to delete character:', error)
      alert('Failed to delete character')
    }
  }

  const handleExport = async (character: Character) => {
    try {
      const response = await fetch(`${API_BASE}/api/characters/${character.id}/export`, {
        method: 'POST',
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${character.name.replace(/\s+/g, '_')}_export.json`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        alert('Failed to export character')
      }
    } catch (error) {
      console.error('Failed to export character:', error)
      alert('Failed to export character')
    }
  }

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_BASE}/api/characters/import`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      
      if (data.success) {
        await loadCharacters()
        alert('Character imported successfully')
      } else {
        alert('Failed to import character: ' + (data.error || 'Unknown error'))
      }
    } catch (error) {
      console.error('Failed to import character:', error)
      alert('Failed to import character')
    } finally {
      // Reset input
      event.target.value = ''
    }
  }

  const filteredCharacters = characters.filter(char =>
    char.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    char.description?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Characters</h1>
          <p className="text-muted-foreground">
            Manage your character profiles with full Character Management System
          </p>
        </div>
        <div className="flex space-x-2">
          <label htmlFor="import-file">
            <Button variant="outline" asChild>
              <span>
                <Upload className="mr-2 h-4 w-4" />
                Import
              </span>
            </Button>
          </label>
          <input
            id="import-file"
            type="file"
            accept=".json"
            onChange={handleImport}
            className="hidden"
          />
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <Button onClick={handleCreate}>
              <Plus className="mr-2 h-4 w-4" />
              Create Character
            </Button>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>
                  {editingCharacter ? 'Edit Character' : 'Create Character'}
                </DialogTitle>
                <DialogDescription>
                  {editingCharacter
                    ? 'Update character information and settings'
                    : 'Create a new character with full Character Management System support'}
                </DialogDescription>
              </DialogHeader>
              <CharacterForm
                character={editingCharacter}
                templates={templates}
                onSave={handleSave}
                onCancel={() => {
                  setIsDialogOpen(false)
                  setEditingCharacter(null)
                }}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search characters..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {isLoading ? (
        <Card>
          <CardContent className="flex items-center justify-center min-h-[400px]">
            <div className="text-center text-muted-foreground">
              <p>Loading characters...</p>
            </div>
          </CardContent>
        </Card>
      ) : filteredCharacters.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center min-h-[400px]">
            <div className="text-center text-muted-foreground">
              <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No characters found</p>
              <p className="text-sm mt-2">
                {searchQuery ? 'Try a different search term' : 'Create your first character to get started'}
              </p>
              {!searchQuery && (
                <Button className="mt-4" onClick={handleCreate}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Character
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredCharacters.map((character) => (
            <Card key={character.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle>{character.name}</CardTitle>
                    {character.age && (
                      <CardDescription className="mt-1">Age: {character.age}</CardDescription>
                    )}
                    {character.description && (
                      <CardDescription className="mt-1 line-clamp-2">
                        {character.description}
                      </CardDescription>
                    )}
                  </div>
                  <div className="flex space-x-1 ml-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleEdit(character)}
                      title="Edit"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleExport(character)}
                      title="Export"
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(character.id)}
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Face References */}
                {character.faceReferences && character.faceReferences.length > 0 ? (
                  <div className="grid grid-cols-2 gap-2">
                    {character.faceReferences.slice(0, 4).map((ref) => {
                      const imageUrl = ref.imageUrl || 
                        (ref.filePath ? `${API_BASE}/api/characters/${character.id}/face-references/${ref.id}/image` : null)
                      
                      return (
                        <div
                          key={ref.id}
                          className="relative aspect-square overflow-hidden rounded-lg border bg-muted"
                        >
                          {imageUrl ? (
                            <img
                              src={imageUrl}
                              alt="Face reference"
                              className="h-full w-full object-cover"
                              onError={(e) => {
                                // Fallback to icon if image fails to load
                                e.currentTarget.style.display = 'none'
                                const parent = e.currentTarget.parentElement
                                if (parent) {
                                  const icon = document.createElement('div')
                                  icon.className = 'flex items-center justify-center h-full'
                                  icon.innerHTML = '<svg class="h-8 w-8 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>'
                                  parent.appendChild(icon)
                                }
                              }}
                            />
                          ) : (
                            <div className="flex items-center justify-center h-full">
                              <ImageIcon className="h-8 w-8 text-muted-foreground" />
                            </div>
                          )}
                          {ref.isPrimary && (
                            <div className="absolute top-1 right-1 bg-primary text-primary-foreground text-xs px-1 rounded">
                              Primary
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-32 border-2 border-dashed rounded-lg">
                    <div className="text-center text-muted-foreground">
                      <ImageIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No face references</p>
                    </div>
                  </div>
                )}

                {/* Character Info */}
                <div className="space-y-2 text-sm">
                  {character.persona && (
                    <div>
                      <span className="font-medium">Persona: </span>
                      <span className="text-muted-foreground">
                        {character.persona.personality?.traits?.slice(0, 3).join(', ') || 'Not set'}
                      </span>
                    </div>
                  )}
                  {character.style && (
                    <div>
                      <span className="font-medium">Style: </span>
                      <span className="text-muted-foreground">
                        {character.style.photography || 'Not set'}
                      </span>
                    </div>
                  )}
                </div>

                {/* Statistics */}
                {(character.stats || character.faceReferenceCount !== undefined || character.mediaCount !== undefined) && (
                  <div className="pt-4 border-t text-sm text-muted-foreground space-y-1">
                    {character.faceReferenceCount !== undefined && (
                      <p>Face References: {character.faceReferenceCount}</p>
                    )}
                    {character.mediaCount !== undefined && (
                      <p>Media Items: {character.mediaCount}</p>
                    )}
                    {character.stats?.totalGenerations !== undefined && (
                      <p>Generations: {character.stats.totalGenerations}</p>
                    )}
                    {character.stats?.lastGeneration && (
                      <p>Last: {new Date(character.stats.lastGeneration).toLocaleDateString()}</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
