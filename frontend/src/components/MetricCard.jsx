const COLOR = {
  stress:     '#DC2626',
  engagement: '#16A34A',
  confidence: '#1D4ED8',
  confusion:  '#D97706',
}

export default function MetricCard({ label, value, state }) {
  const pct   = Math.round((value ?? 0) * 100)
  const color = COLOR[label.toLowerCase()] ?? '#64748B'

  return (
    <div className="metric-card fade-in">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{pct}<small style={{ fontSize: 16, color: 'var(--text-muted)' }}>%</small></span>
      <div className="metric-bar-track">
        <div
          className="metric-bar-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      {state && <span className="metric-state">{state}</span>}
    </div>
  )
}