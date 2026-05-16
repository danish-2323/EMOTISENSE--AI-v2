import { useState, useEffect } from 'react'

function grade(avgFocus) {
  if (avgFocus >= 75) return { g: 'A', color: '#22c55e', label: 'Excellent' }
  if (avgFocus >= 60) return { g: 'B', color: '#3b82f6', label: 'Good' }
  if (avgFocus >= 45) return { g: 'C', color: '#f59e0b', label: 'Fair' }
  return { g: 'D', color: '#ef4444', label: 'Needs Work' }
}

export default function StudyReport({ stats, history, plan }) {
  const [report,   setReport]   = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [exported, setExported] = useState(false)
  const [screenshots, setScreenshots] = useState([])

  // Load screenshots from localStorage
  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem('emotisense_screenshots') || '[]')
    setScreenshots(stored)
  }, [])

  const avgStress  = history.length ? history.reduce((s,d) => s + (d.fused?.stress      ?? 0), 0) / history.length : 0
  const avgEngage  = history.length ? history.reduce((s,d) => s + (d.fused?.engagement  ?? 0), 0) / history.length : 0
  const avgConf    = history.length ? history.reduce((s,d) => s + (d.fused?.confidence  ?? 0), 0) / history.length : 0
  const avgFocus   = Math.round(avgEngage * 100)
  const g          = grade(avgFocus)

  // Peak moments
  const peakStress = history.length ? history.reduce((a,b) => (b.fused?.stress ?? 0) > (a.fused?.stress ?? 0) ? b : a, history[0]) : null
  const peakFocus  = history.length ? history.reduce((a,b) => (b.fused?.engagement ?? 0) > (a.fused?.engagement ?? 0) ? b : a, history[0]) : null

  // Distraction log — combine state transitions AND screenshot captures
  const stateDistractions = history.reduce((acc, d, i) => {
    const prevState = history[i-1]?.study_state
    const currState = d.study_state
    
    if (currState === 'Distracted' && prevState !== 'Distracted') {
      const faceFocus = Math.round((d.fused?.engagement ?? 0) * 100)
      const screenFocus = d.screen_focus ?? null
      
      // Determine distraction type
      let type = 'Unknown'
      if (faceFocus < 40 && screenFocus !== null && screenFocus < 40) {
        type = 'Both (Face + Screen)'
      } else if (faceFocus < 40) {
        type = 'Face Disengagement'
      } else if (screenFocus !== null && screenFocus < 40) {
        type = 'Wrong App/Website'
      }
      
      acc.push({ 
        second: i, 
        state: currState,
        type,
        faceFocus,
        screenFocus,
        timestamp: d.ts
      })
    }
    return acc
  }, [])
  
  // Add screenshot-based distractions
  const screenshotDistractions = screenshots.map(s => ({
    timestamp: s.timestamp,
    type: s.faceFocus < 40 && s.screenFocus < 40 ? 'Both (Face + Screen)' :
          s.faceFocus < 40 ? 'Face Disengagement' : 'Wrong App/Website',
    faceFocus: s.faceFocus,
    screenFocus: s.screenFocus,
    hasScreenshot: true
  }))
  
  // Merge and deduplicate by timestamp (within 5 seconds)
  const allDistractions = [...stateDistractions, ...screenshotDistractions]
  const distractions = allDistractions.filter((d, i, arr) => {
    const dTime = new Date(d.timestamp).getTime()
    return !arr.slice(0, i).some(prev => {
      const pTime = new Date(prev.timestamp).getTime()
      return Math.abs(dTime - pTime) < 5000
    })
  }).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
  
  // High stress moments
  const stressMoments = history.reduce((acc, d, i) => {
    const stress = (d.fused?.stress ?? 0) * 100
    if (stress > 70) {
      acc.push({
        second: i,
        stress: Math.round(stress),
        timestamp: d.ts
      })
    }
    return acc
  }, [])

  useEffect(() => {
    if (stats && history.length > 5) fetchReport()
  }, [stats])

  async function fetchReport() {
    setLoading(true)
    try {
      const res  = await fetch('https://emotisense-e6z2.onrender.com/study/coach/report', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          plan,
          stats: { avg_stress: avgStress, avg_engagement: avgEngage, distractions: distractions.length, ...stats },
        }),
      })
      const data = await res.json()
      setReport(data.report)
      saveToHistory(data.report)
    } catch { setReport(null) }
    finally  { setLoading(false) }
  }

  function saveToHistory(reportText) {
    const sessions = JSON.parse(localStorage.getItem('emotisense_sessions') || '[]')
    sessions.unshift({
      id:          Date.now(),
      date:        new Date().toLocaleDateString(),
      subject:     plan?.subject || 'Unknown',
      duration:    stats?.duration || '—',
      grade:       g.g,
      avgFocus,
      avgStress:   Math.round(avgStress * 100),
      report:      reportText,
      plan,
    })
    localStorage.setItem('emotisense_sessions', JSON.stringify(sessions.slice(0, 50)))
  }

  async function exportPDF() {
    try {
      const res  = await fetch('http://localhost:8000/session/export/pdf', { method: 'POST' })
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      Object.assign(document.createElement('a'), { href: url, download: 'study_report.pdf' }).click()
      setExported(true)
    } catch { alert('PDF export failed — check backend.') }
  }

  if (!stats && history.length < 5) {
    return (
      <div className="idle-overlay fade-in">
        <h3>No session data yet</h3>
        <p>Complete a study session to see your report.</p>
      </div>
    )
  }

  return (
    <div className="study-report fade-in">

      {/* Grade banner */}
      <div className="report-grade-banner" style={{ borderColor: g.color }}>
        <span className="report-grade" style={{ color: g.color }}>{g.g}</span>
        <div>
          <p className="report-grade-label">{g.label} Session</p>
          <p className="report-grade-sub">{plan?.subject || 'Study Session'} · {stats?.duration || '—'}</p>
        </div>
      </div>

      {/* Stats row */}
      <div className="report-stats-row">
        {[
          { label: 'Avg Focus',       val: `${avgFocus}%`, icon: '🎯' },
          { label: 'Avg Stress',      val: `${Math.round(avgStress * 100)}%`, icon: '😰' },
          { label: 'Avg Confidence',  val: `${Math.round(avgConf * 100)}%`, icon: '💪' },
          { label: 'Distractions',    val: distractions.length, icon: '⚠️' },
          { label: 'Data Points',     val: history.length, icon: '📊' },
          { label: 'Duration',        val: stats?.duration || '—', icon: '⏱' },
        ].map(s => (
          <div key={s.label} className="report-stat-chip">
            <span className="rsc-icon">{s.icon}</span>
            <span className="rsc-label">{s.label}</span>
            <span className="rsc-val">{s.val}</span>
          </div>
        ))}
      </div>

      {/* Peak moments */}
      {peakStress && peakFocus && (
        <div className="card">
          <div className="card-header"><span className="card-title">Peak Moments</span></div>
          <div className="card-body">
            <div className="peak-moments-grid">
              <div className="peak-moment">
                <span className="peak-icon" style={{ background: '#FEE2E2', color: '#DC2626' }}>🔥</span>
                <div className="peak-info">
                  <span className="peak-label">Highest Stress</span>
                  <span className="peak-val">{Math.round((peakStress.fused?.stress ?? 0) * 100)}%</span>
                  <span className="peak-time">~{Math.floor(history.indexOf(peakStress) / 60)}m {history.indexOf(peakStress) % 60}s</span>
                </div>
              </div>
              <div className="peak-moment">
                <span className="peak-icon" style={{ background: '#D1FAE5', color: '#059669' }}>⭐</span>
                <div className="peak-info">
                  <span className="peak-label">Peak Focus</span>
                  <span className="peak-val">{Math.round((peakFocus.fused?.engagement ?? 0) * 100)}%</span>
                  <span className="peak-time">~{Math.floor(history.indexOf(peakFocus) / 60)}m {history.indexOf(peakFocus) % 60}s</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Distraction log */}
      {distractions.length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">📋 Distraction Log</span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{distractions.length} incidents</span>
          </div>
          <div className="card-body">
            <div className="distraction-table">
              <div className="distraction-header">
                <span>Time</span>
                <span>Type</span>
                <span>Face</span>
                <span>Screen</span>
                <span>📸</span>
              </div>
              {distractions.slice(0, 10).map((d, i) => (
                <div key={i} className="distraction-row">
                  <span className="dist-time">
                    {d.second !== undefined ? `~${Math.floor(d.second / 60)}m ${d.second % 60}s` : new Date(d.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="dist-type" data-type={d.type}>{d.type}</span>
                  <span className="dist-metric" style={{ color: d.faceFocus < 40 ? '#DC2626' : '#059669' }}>
                    {d.faceFocus}%
                  </span>
                  <span className="dist-metric" style={{ color: d.screenFocus !== null && d.screenFocus < 40 ? '#DC2626' : '#059669' }}>
                    {d.screenFocus !== null ? `${d.screenFocus}%` : '—'}
                  </span>
                  <span style={{ fontSize: 14 }}>{d.hasScreenshot ? '✅' : '—'}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* High stress moments */}
      {stressMoments.length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">😰 High Stress Moments</span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{stressMoments.length} incidents</span>
          </div>
          <div className="card-body">
            <div className="stress-moments-list">
              {stressMoments.slice(0, 8).map((m, i) => (
                <div key={i} className="stress-moment-row">
                  <span className="stress-icon">🔥</span>
                  <div className="stress-info">
                    <span className="stress-time">~{Math.floor(m.second / 60)}m {m.second % 60}s</span>
                    <span className="stress-level" style={{ color: m.stress > 80 ? '#DC2626' : '#F59E0B' }}>
                      {m.stress}% stress
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* AI Report */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">🤖 AI Coach Analysis</span>
          {!report && !loading && (
            <button className="btn-sm btn-primary" onClick={fetchReport}>Generate</button>
          )}
        </div>
        <div className="card-body">
          {loading && <p className="report-loading">Generating personalised insights…</p>}
          {report  && <p className="report-text">{report}</p>}
          {!report && !loading && <p className="report-hint">Click Generate to get Claude-powered insights.</p>}
        </div>
      </div>

      {/* Export */}
      <div style={{ display: 'flex', gap: 10 }}>
        <button className="btn-primary" onClick={exportPDF}>
          {exported ? '✅ Downloaded' : '📄 Export PDF'}
        </button>
      </div>
    </div>
  )
}
