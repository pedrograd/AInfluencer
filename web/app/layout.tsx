import type { Metadata } from 'next'
import './globals.css'
import { Header } from '@/components/layout/Header'
import { KeyboardShortcutsProvider } from '@/components/keyboard-shortcuts-provider'
import ThemeToggle from './components/ThemeToggle'

export const metadata: Metadata = {
  title: 'AInfluencer - Ultra-Realistic AI Media Generator',
  description: 'Generate ultra-realistic images and videos indistinguishable from real media',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background font-sans antialiased">
        <KeyboardShortcutsProvider>
          <Header />
          <main className="container py-6">{children}</main>
          <ThemeToggle />
        </KeyboardShortcutsProvider>
      </body>
    </html>
  )
}
