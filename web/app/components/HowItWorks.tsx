export default function HowItWorks() {
  const steps = [
    {
      number: '1',
      title: 'Character Setup',
      description: 'Create character profiles with appearance details and reference images',
    },
    {
      number: '2',
      title: 'Prompt Generation',
      description: 'Automatically generate diverse prompts based on character profiles',
    },
    {
      number: '3',
      title: 'Workflow Creation',
      description: 'Generate ComfyUI workflows optimized for your character and models',
    },
    {
      number: '4',
      title: 'Image Generation',
      description: 'Batch generate images using ComfyUI API with automatic queue management',
    },
    {
      number: '5',
      title: 'Post-Processing',
      description: 'Optional upscaling and face restoration for final output',
    },
  ]

  return (
    <section id="how-it-works" className="section" style={{ background: 'var(--bg-secondary)' }}>
      <div className="container">
        <h2 style={{ fontSize: '2.5rem', marginBottom: '3rem', textAlign: 'center' }}>
          How It Works
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '2rem' }}>
          {steps.map((step) => (
            <div key={step.number} className="card">
              <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--accent)', marginBottom: '1rem' }}>
                {step.number}
              </div>
              <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{step.title}</h3>
              <p style={{ color: 'var(--text-secondary)' }}>{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
