import { AlertTriangle, Camera } from 'lucide-react'
import MetricCard   from './MetricCard'
import StressGauge  from './StressGauge'
import TimelineChart from './TimelineChart'

const EMOTION_COLORS = {
  happy:    '#16A34A',
  neutral:  '#64748B',
  sad:      '#2563EB',
  angry:    '#DC2626',
  fear:     '#9333EA',
  surprise: '#D97706',
}

export default function Dashboard({ data, history, sessionActive }) {
  const fused = data?.fused ?? {}
  const face  = data?.face  ?? {}
  const frame = data?.frame

  if (!sessionActive) {
    return (
      <div className="idle-overlay fade-in">
        <Camera size={40} strokeWidth={1} />
        <h3>No active session</h3>
        <p>Click <strong>Start Session</strong> in the sidebar to begin real-time emotion monitoring.</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }} className="fade-in">

      {/* Alert */}
      {data?.alert && (
        <div className="alert-banner">
          <AlertTriangle size={16} />
          High stress detected — sustained for {'>'}5 seconds
        </div>
      )}

      {/* Metric cards */}
      <div className="metrics-grid">
        <MetricCard label="Stress"     value={fused.stress}     state={fused.dominant_state} />
        <MetricCard label="Engagement" value={fused.engagement} />
        <MetricCard label="Confidence" value={fused.confidence} />
        <MetricCard label="Confusion"  value={fused.confusion}  />
      </div>

      {/* Main row: feed + right panel */}
      <div className="dashboard-grid">

        {/* Left: video feed */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <div className="card-header">
              <span className="card-title">Video Feed</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11,
                color: data?.simulation ? 'var(--warn)' : 'var(--ok)' }}>
                <span className={data?.simulation ? '' : 'live-dot'} />
                {data?.simulation ? 'Simulation' : 'Live'}
              </div>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              <div className="feed-panel">
                {frame
                  ? <img src={`data:image/jpeg;base64,${frame}`} alt="live feed" />
                  : (
                    <div className="feed-idle">
                      <Camera size={32} strokeWidth={1} />
                      <span>{data?.simulation ? 'Simulation mode active' : 'Connecting camera…'}</span>
                    </div>
                  )
                }
                {/* Dominant state badge */}
                {fused.dominant_state && (
                  <div className="feed-badge">
                    <span className={`state-badge ${fused.dominant_state}`}>
                      {fused.dominant_state}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Emotion Timeline</span>
              <span className="timestamp">{data?.ts ? new Date(data.ts).toLocaleTimeString() : '—'}</span>
            </div>
            <div className="card-body" style={{ paddingTop: 8 }}>
              <TimelineChart history={history} />
            </div>
          </div>
        </div>

        {/* Right panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Stress gauge */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Stress Gauge</span>
            </div>
            <div className="card-body" style={{ display: 'flex', justifyContent: 'center' }}>
              <StressGauge value={fused.stress ?? 0} />
            </div>
          </div>

          {/* Emotion breakdown */}
          <div className="card" style={{ flex: 1 }}>
            <div className="card-header">
              <span className="card-title">Face Emotions</span>
              <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                smoothed · 5-frame avg
              </span>
            </div>
            <div className="card-body">
              <div className="emotion-list">
                {Object.entries(face)
                  .sort(([,a], [,b]) => b - a)
                  .map(([name, val]) => (
                    <div key={name} className="emotion-row">
                      <span className="emotion-name">{name}</span>
                      <div className="emotion-track">
                        <div
                          className="emotion-fill"
                          style={{
                            width: `${Math.round(val * 100)}%`,
                            background: EMOTION_COLORS[name] ?? '#64748B',
                          }}
                        />
                      </div>
                      <span className="emotion-pct">{Math.round(val * 100)}%</span>
                    </div>
                  ))
                }
              </div>

              {/* Audio stress */}
              <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between',
                  fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                  <span style={{ fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase' }}>
                    Audio Stress
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>
                    {Math.round((data?.audio_stress ?? 0) * 100)}%
                  </span>
                </div>
                <div className="emotion-track" style={{ height: 8 }}>
                  <div
                    className="emotion-fill"
                    style={{
                      width: `${Math.round((data?.audio_stress ?? 0) * 100)}%`,
                      background: '#DC2626',
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}