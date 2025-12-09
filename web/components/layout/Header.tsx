'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Image, Video, Library, Users, Home, Settings, Wand2, Shield, CheckCircle2, Zap, Share2, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Generate Image', href: '/generate/image', icon: Image },
  { name: 'Generate Video', href: '/generate/video', icon: Video },
  { name: 'Prompts', href: '/prompts', icon: Wand2 },
  { name: 'Quality', href: '/quality', icon: CheckCircle2 },
  { name: 'Anti-Detection', href: '/anti-detection', icon: Shield },
  { name: 'Platforms', href: '/platforms', icon: Share2 },
  { name: 'Automation', href: '/automation', icon: Zap },
  { name: 'Media Library', href: '/library', icon: Library },
  { name: 'Characters', href: '/characters', icon: Users },
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'Setup', href: '/setup', icon: Settings },
  { name: 'Help', href: '/help', icon: HelpCircle },
]

export function Header() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center">
        <div className="mr-4 flex">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <span className="text-xl font-bold">AInfluencer</span>
          </Link>
        </div>
        <nav className="flex items-center space-x-6 text-sm font-medium">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center space-x-2 transition-colors hover:text-foreground/80',
                  isActive ? 'text-foreground' : 'text-foreground/60'
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
