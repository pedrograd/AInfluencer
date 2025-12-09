'use client'

import { useEffect, useState } from 'react'
import { BestPracticesDashboard } from '@/components/best-practices/BestPracticesDashboard'
import { PracticeValidator } from '@/components/best-practices/PracticeValidator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card } from '@/components/ui/card'

export default function BestPracticesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Best Practices</h1>
        <p className="text-gray-600">
          Monitor and enforce best practices across content creation, technical implementation, quality, security, and performance
        </p>
      </div>

      <Tabs defaultValue="dashboard" className="space-y-6">
        <TabsList>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="validator">Prompt Validator</TabsTrigger>
          <TabsTrigger value="guidelines">Guidelines</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <BestPracticesDashboard />
        </TabsContent>

        <TabsContent value="validator">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h2 className="text-xl font-bold mb-4">Validate Your Prompt</h2>
              <PracticeValidator />
            </Card>
            
            <Card className="p-6">
              <h2 className="text-xl font-bold mb-4">Best Practices Guide</h2>
              <div className="space-y-4 text-sm">
                <div>
                  <h3 className="font-semibold mb-2">Content Creation</h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-600">
                    <li>Use detailed, specific prompts</li>
                    <li>Include quality modifiers</li>
                    <li>Always use negative prompts</li>
                    <li>Maintain face consistency</li>
                    <li>Always post-process content</li>
                    <li>Remove all metadata</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="font-semibold mb-2">Quality Standards</h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-600">
                    <li>Set quality thresholds (8.0+)</li>
                    <li>Test all content before publishing</li>
                    <li>Use automated scoring</li>
                    <li>Manual review when needed</li>
                  </ul>
                </div>
              </div>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="guidelines">
          <GuidelinesView />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function GuidelinesView() {
  const [guidelines, setGuidelines] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/best-practices/guidelines')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setGuidelines(data.data)
        }
      })
      .catch(err => console.error('Failed to load guidelines:', err))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="text-center py-8">Loading guidelines...</div>
  }

  if (!guidelines) {
    return <div className="text-center py-8 text-gray-600">No guidelines available</div>
  }

  return (
    <div className="space-y-6">
      {Object.entries(guidelines).map(([category, practices]: [string, any]) => (
        <Card key={category} className="p-6">
          <h2 className="text-2xl font-bold mb-4 capitalize">{category}</h2>
          
          {Object.entries(practices).map(([practiceName, practice]: [string, any]) => (
            <div key={practiceName} className="mb-6">
              <h3 className="text-xl font-semibold mb-3 capitalize">{practiceName.replace(/_/g, ' ')}</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold text-green-700 mb-2">✓ Do:</h4>
                  <ul className="list-disc list-inside space-y-1 text-gray-700">
                    {practice.do?.map((item: string, index: number) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-semibold text-red-700 mb-2">✗ Don't:</h4>
                  <ul className="list-disc list-inside space-y-1 text-gray-700">
                    {practice.dont?.map((item: string, index: number) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </Card>
      ))}
    </div>
  )
}

