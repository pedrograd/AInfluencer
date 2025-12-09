'use client'

import { useEffect, useState } from 'react'
import { Sun, Moon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/Tooltip'

type Theme = 'dark' | 'light'

const applyTheme = (nextTheme: Theme) => {
  const root = document.documentElement
  root.dataset.theme = nextTheme
  root.classList.toggle('dark', nextTheme === 'dark')
  localStorage.setItem('theme', nextTheme)
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>('dark')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return
    const savedTheme = (localStorage.getItem('theme') as Theme | null) ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    setTheme(savedTheme)
    applyTheme(savedTheme)
    setMounted(true)
  }, [])

  const toggleTheme = () => {
    if (typeof window === 'undefined') return
    const nextTheme: Theme = theme === 'dark' ? 'light' : 'dark'
    setTheme(nextTheme)
    applyTheme(nextTheme)
  }

  if (!mounted) return null

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="outline"
            size="icon"
            onClick={toggleTheme}
            className="fixed right-4 bottom-4 md:top-4 md:bottom-auto h-10 w-10 z-50"
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          >
            {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </Button>
        </TooltipTrigger>
        <TooltipContent side="left">
          Toggle {theme === 'dark' ? 'light' : 'dark'} mode
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
