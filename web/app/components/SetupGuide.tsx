'use client'

import { useState } from 'react'
import CodeBlock from './CodeBlock'

export default function SetupGuide() {
  const commands = {
    setup: '.\auto-complete-setup.ps1',
    createCharacter: '.\create-character-config.ps1 -CharacterName "MyModel"',
    generatePrompts: 'py generate-prompt-auto.py characters\MyModel\config.json',
    startComfyUI: 'cd ComfyUI\npy main.py',
    runFullAuto: '.\full-auto-generate.ps1 -CharacterName "MyModel" -ImageCount 10',
  }

  return (
    <section id="setup" className="section">
      <div className="container">
        <h2 style={{ fontSize: '2.5rem', marginBottom: '2rem' }}>Setup Guide</h2>
        <p style={{ marginBottom: '2rem', color: 'var(--text-secondary)' }}>
          Windows-specific setup instructions for AInfluencer pipeline.
        </p>

        <div style={{ marginBottom: '3rem' }}>
          <h3 style={{ fontSize: '1.8rem', marginBottom: '1rem' }}>Prerequisites</h3>
          <ul style={{ listStyle: 'disc', paddingLeft: '2rem', lineHeight: '2' }}>
            <li>Windows 10/11</li>
            <li>Python 3.11 or 3.12 (recommended)</li>
            <li>Git (for cloning ComfyUI)</li>
            <li>NVIDIA GPU (recommended, CPU supported)</li>
          </ul>
        </div>

        <div style={{ marginBottom: '3rem' }}>
          <h3 style={{ fontSize: '1.8rem', marginBottom: '1rem' }}>Quick Commands</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>1. Initial Setup</h4>
              <CodeBlock code={commands.setup} />
            </div>
            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>2. Create Character</h4>
              <CodeBlock code={commands.createCharacter} />
            </div>
            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>3. Generate Prompts</h4>
              <CodeBlock code={commands.generatePrompts} />
            </div>
            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>4. Start ComfyUI</h4>
              <CodeBlock code={commands.startComfyUI} />
            </div>
            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>5. Run Full Automation</h4>
              <CodeBlock code={commands.runFullAuto} />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
