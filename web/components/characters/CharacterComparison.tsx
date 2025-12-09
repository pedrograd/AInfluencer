'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { backendAPI } from '@/lib/api/backend'
import { Loader2, Users, CheckCircle2 } from 'lucide-react'

export function CharacterComparison() {
  const [characterIds, setCharacterIds] = useState<string>('')
  const [processing, setProcessing] = useState(false)
  const [comparison, setComparison] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleCompare = async () => {
    const ids = characterIds.split(',').map(id => id.trim()).filter(Boolean)
    
    if (ids.length < 2) {
      setError('Please provide at least 2 character IDs (comma-separated)')
      return
    }

    setProcessing(true)
    setError(null)
    setComparison(null)

    try {
      const response = await backendAPI.compareCharacters(ids)
      const success = (response as any)?.success ?? true
      const data = (response as any)?.data ?? response
      const errorMessage = (response as any)?.error?.message

      if (success) {
        setComparison(data)
      } else {
        setError(errorMessage || 'Character comparison failed')
      }
    } catch (err: any) {
      setError(err.message || 'Character comparison failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Users className="h-5 w-5" />
          <span>Character Comparison</span>
        </CardTitle>
        <CardDescription>
          Compare multiple characters side-by-side
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Character IDs (comma-separated)</label>
          <Input
            value={characterIds}
            onChange={(e) => setCharacterIds(e.target.value)}
            placeholder="char-id-1, char-id-2, char-id-3"
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-sm text-red-800 dark:text-red-200">
            {error}
          </div>
        )}

        {comparison && (
          <div className="space-y-3">
            <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
              <div className="flex items-center space-x-2 text-green-800 dark:text-green-200 mb-2">
                <CheckCircle2 className="h-4 w-4" />
                <span className="text-sm font-medium">Comparison Results</span>
              </div>
              
              <div className="space-y-2 text-sm">
                {comparison.characters?.map((char: any, idx: number) => (
                  <div key={idx} className="p-2 bg-white dark:bg-gray-800 rounded">
                    <div className="font-medium">{char.name}</div>
                    <div className="text-xs text-muted-foreground">
                      Age: {char.age || 'N/A'} | Face References: {char.face_references_count || 0}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <Button
          onClick={handleCompare}
          disabled={processing || !characterIds}
          className="w-full"
        >
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Comparing...
            </>
          ) : (
            'Compare Characters'
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
