'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { usePathname } from 'next/navigation'

interface KeyboardShortcutsProps {
  enabled?: boolean
}

export function KeyboardShortcuts({ enabled = true }: KeyboardShortcutsProps) {
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Only trigger if not typing in an input/textarea
      const target = e.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return
      }

      // Ctrl+G: Generate image
      if (e.ctrlKey && e.key === 'g') {
        e.preventDefault()
        router.push('/generate/image')
      }

      // Ctrl+V: Generate video
      if (e.ctrlKey && e.key === 'v') {
        e.preventDefault()
        router.push('/generate/video')
      }

      // Ctrl+L: Open library
      if (e.ctrlKey && e.key === 'l') {
        e.preventDefault()
        router.push('/library')
      }

      // Ctrl+C: Create character
      if (e.ctrlKey && e.key === 'c') {
        e.preventDefault()
        router.push('/characters')
      }

      // Ctrl+S: Save (context-dependent)
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault()
        // This will be handled by individual pages
        const event = new CustomEvent('keyboard-save')
        window.dispatchEvent(event)
      }

      // Esc: Close dialogs
      if (e.key === 'Escape') {
        const event = new CustomEvent('keyboard-escape')
        window.dispatchEvent(event)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [enabled, router, pathname])

  return null
}
