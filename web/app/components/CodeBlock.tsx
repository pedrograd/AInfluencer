'use client'

import { useState } from 'react'

export default function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="code-block" style={{ position: 'relative' }}>
      <button
        onClick={copyToClipboard}
        className="copy-btn"
        style={{
          position: 'absolute',
          top: '0.5rem',
          right: '0.5rem',
          padding: '0.25rem 0.75rem',
          background: 'var(--bg-primary)',
          border: '1px solid var(--border)',
          borderRadius: '4px',
          color: 'var(--text-primary)',
          cursor: 'pointer',
          fontSize: '0.85em',
        }}
      >
        {copied ? '✓ Copied' : 'Copy'}
      </button>
      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{code}</pre>
    </div>
  )
}
