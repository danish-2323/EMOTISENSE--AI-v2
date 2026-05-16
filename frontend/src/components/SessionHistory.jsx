import { useState, useEffect } from 'react'

const GRADE_COLOR = { A: '#22c55e', B: '#3b82f6', C: '#f59e0b', D: '#ef4444' }

export default function SessionHistory() {
  const [sessions,  setSessions]  = useState([])
  const [selected,  setSelected]  = useState(null)

  useEffect(() => {
    setSessions(JSON.parse(localStorage.getItem('emotisense_sessions') || '[]'))
  }, [])

  function clearHistory() {
    if (!confirm('Delete all session history?')) return
    localStorage.removeItem('emotisense_sessions')
    setSessions([])
    setSelected(null)
  }

  if (sessions.length === 0) {
    return (
      <div className="idle-overlay fade-in">
        <h3>No sessions yet</h3>
        <p>Complete a study session to see your history here.</p>
      </div>
    )
  }

  if (selected) {
    return (
      <div className="history-detail fade-in">
        <button className="btn-sm btn-ghost" onClick={() => setSelected(null)}>← Back to History</button>
        
        <div className="report-grade-banner" style={{ borderColor: GRADE_COLOR[selected.grade] }}>
          <span className="report-grade" style={{ color: GRADE_COLOR[selected.grade] }}>{selected.grade}</span>
          <div>
            <p className="report-grade-label">{selected.subject}</p>
            <p className="report-grade-sub">{selected.date} · {selected.duration} · {selected.plan?.mode || 'Study Session'}</p>
          </div>
        </div>
        
        <div className="report-stats-row">
          {[
            { label: 'Focus Score', val: `${selected.avgFocus}%`, icon: '🎯' },
            { label: 'Stress Level', val: `${selected.avgStress}%`, icon: '😰' },
            { label: 'Grade', val: selected.grade, icon: '🏆' },
          ].map(s => (
            <div key={s.label} className="report-stat-chip">
              <span className="rsc-icon">{s.icon}</span>
              <span className="rsc-label">{s.label}</span>
              <span className="rsc-val">{s.val}</span>
            </div>
          ))}
        </div>
        
        {selected.plan?.goals && (
          <div className="card">
            <div className="card-header"><span className="card-title">Session Goals</span></div>
            <div className="card-body">
              <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{selected.plan.goals}</p>
            </div>
          </div>
        )}
        
        {selected.report && (
          <div className="card">
            <div className="card-header"><span className="card-title">🤖 AI Analysis</span></div>
            <div className="card-body"><p className="report-text">{selected.report}</p></div>
          </div>
        )}
      </div>
    )
  }

  // Weekly focus trend (last 7 sessions)
  const trend = sessions.slice(0, 7).reverse()

  return (
    <div className="history-shell fade-in">
      <div className="history-header">
        <div>
          <h3 className="history-title">📊 Session History</h3>
          <p className="history-subtitle">{sessions.length} completed session{sessions.length !== 1 ? 's' : ''}</p>
        </div>
        <button className="btn-sm btn-danger" onClick={clearHistory}>🗑 Clear All</button>
      </div>

      {/* Trend bar chart */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">📈 Focus Trend</span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Last {trend.length} sessions</span>
        </div>
        <div className="card-body">
          <div className="trend-chart">
            {trend.map((s, i) => (
              <div key={i} className="trend-bar-wrap">
                <div className="trend-bar" style={{ height: `${s.avgFocus}%`, background: GRADE_COLOR[s.grade] }} />
                <span className="trend-label">{s.grade}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Session list */}
      <div className="history-list">
        {sessions.map(s => (
          <div key={s.id} className="history-row" onClick={() => setSelected(s)}>
            <span className="history-grade" style={{ color: GRADE_COLOR[s.grade] }}>{s.grade}</span>
            <div className="history-info">
              <span className="history-subject">{s.subject}</span>
              <span className="history-meta">{s.date} · {s.duration} · Focus {s.avgFocus}%</span>
            </div>
            <span className="history-arrow">›</span>
          </div>
        ))}
      </div>
    </div>
  )
}
