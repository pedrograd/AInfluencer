export default function Hero() {
  return (
    <section className="section" style={{ paddingTop: '6rem', textAlign: 'center' }}>
      <div className="container">
        <h1 style={{ fontSize: '3.5rem', marginBottom: '1rem', fontWeight: 700 }}>
          AInfluencer
        </h1>
        <p style={{ fontSize: '1.5rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
          Automated Creator Image Pipeline
        </p>
        <p style={{ fontSize: '1.1rem', maxWidth: '800px', margin: '0 auto 2rem', lineHeight: '1.8' }}>
          Professional AI-powered image generation pipeline for content creators.
          Generate consistent, high-quality images with automated workflows.
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href="#setup" className="btn">Get Started</a>
          <a href="#troubleshooting" className="btn btn-secondary">Troubleshooting</a>
        </div>
      </div>
    </section>
  )
}
