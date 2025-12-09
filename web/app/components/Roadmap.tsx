export default function Roadmap() {
  const roadmapItems = [
    {
      status: 'completed',
      title: 'Core Pipeline',
      items: ['Character management', 'Prompt generation', 'Workflow automation', 'API integration'],
    },
    {
      status: 'completed',
      title: 'Windows Compatibility',
      items: ['UTF-8 encoding fixes', 'Python version detection', 'Model fallbacks', 'Error handling'],
    },
    {
      status: 'in-progress',
      title: 'Enhanced Features',
      items: ['Batch processing', 'Quality assurance', 'Metadata management', 'Platform integration'],
    },
    {
      status: 'planned',
      title: 'Advanced Features',
      items: ['Video generation', 'Face consistency improvements', 'Style transfer', 'Multi-model support'],
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'var(--success)'
      case 'in-progress':
        return 'var(--warning)'
      default:
        return 'var(--text-secondary)'
    }
  }

  return (
    <section id="roadmap" className="section">
      <div className="container">
        <h2 style={{ fontSize: '2.5rem', marginBottom: '2rem' }}>Roadmap</h2>
        <p style={{ marginBottom: '3rem', color: 'var(--text-secondary)' }}>
          Current status and planned features for AInfluencer.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem' }}>
          {roadmapItems.map((item, idx) => (
            <div key={idx} className="card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <div
                  style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    background: getStatusColor(item.status),
                  }}
                />
                <h3 style={{ fontSize: '1.3rem', textTransform: 'uppercase', color: getStatusColor(item.status) }}>
                  {item.status}
                </h3>
              </div>
              <h4 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>{item.title}</h4>
              <ul style={{ listStyle: 'disc', paddingLeft: '1.5rem', lineHeight: '1.8' }}>
                {item.items.map((subItem, subIdx) => (
                  <li key={subIdx} style={{ color: 'var(--text-secondary)' }}>
                    {subItem}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
