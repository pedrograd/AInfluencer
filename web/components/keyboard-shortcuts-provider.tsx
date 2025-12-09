'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { KeyboardShortcuts } from './keyboard-shortcuts'

export function KeyboardShortcutsProvider({ children }: { children: React.ReactNode }) {
  const [enabled, setEnabled] = useState(true)

  useEffect(() => {
    // Load keyboard shortcuts setting
    const loadSetting = async () => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const response = await fetch(`${API_BASE}/api/settings`)
        const data = await response.json()
        if (data.success && data.data?.ui?.keyboard_shortcuts !== undefined) {
          setEnabled(data.data.ui.keyboard_shortcuts)
        }
      } catch (error) {
        console.error('Failed to load keyboard shortcuts setting:', error)
      }
    }
    loadSetting()
  }, [])

  return (
    <>
      <KeyboardShortcuts enabled={enabled} />
      {children}
    </>
  )
}
