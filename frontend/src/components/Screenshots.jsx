import { useState, useEffect } from 'react'

export default function Screenshots() {
  const [screenshots, setScreenshots] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem('emotisense_screenshots') || '[]')
    setScreenshots(stored.reverse())  // Most recent first
  }, [])

  function clearAll() {
    if (!confirm('Delete all captured screenshots?')) return
    localStorage.removeItem('emotisense_screenshots')
    setScreenshots([])
  }

  if (screenshots.length === 0) {
    return (
      <div className="idle-overlay fade-in">
        <h3>No screenshots captured yet</h3>
        <p>Screenshots are automatically captured during distraction or high stress moments.</p>
      </div>
    )
  }

  if (selected) {
    return (
      <div className="screenshot-detail fade-in">
        <button className="btn-sm btn-ghost" onClick={() => setSelected(null)}>← Back to Gallery</button>
        
        <div className="screenshot-detail-card">
          <div className="screenshot-detail-header">
            <div>
              <h3 className="screenshot-detail-title">
                {selected.type === 'distraction' ? '🚨 Distraction Detected' : '😰 High Stress Moment'}
              </h3>
              <p className="screenshot-detail-time">{new Date(selected.timestamp).toLocaleString()}</p>
            </div>
            <div className="screenshot-detail-scores">
              <div className="score-badge" style={{ background: selected.faceFocus < 40 ? '#FEE2E2' : '#D1FAE5', color: selected.faceFocus < 40 ? '#991B1B' : '#065F46' }}>
                Face: {selected.faceFocus}%
              </div>
              <div className="score-badge" style={{ background: selected.screenFocus < 40 ? '#FEE2E2' : '#D1FAE5', color: selected.screenFocus < 40 ? '#991B1B' : '#065F46' }}>
                Screen: {selected.screenFocus}%
              </div>
              <div className="score-badge" style={{ background: selected.stressLevel > 70 ? '#FEE2E2' : '#FEF3C7', color: selected.stressLevel > 70 ? '#991B1B' : '#92400E' }}>
                Stress: {selected.stressLevel}%
              </div>
            </div>
          </div>
          
          {/* Dual image display: Screen + Face */}
          <div className="screenshot-dual-view">
            <div className="screenshot-view-section">
              <div className="screenshot-view-label">🖥 Screen Capture</div>
              <img src={selected.screenImage} alt="Screen" className="screenshot-detail-image" />
            </div>
            {selected.faceImage && (
              <div className="screenshot-view-section">
                <div className="screenshot-view-label">😊 Face Reaction</div>
                <img src={selected.faceImage} alt="Face" className="screenshot-detail-image screenshot-face-image" />
              </div>
            )}
          </div>
          
          <div className="screenshot-detail-info">
            <div className="screenshot-info-row">
              <span className="screenshot-info-label">Detected App:</span>
              <span className="screenshot-info-val">{selected.detectedApp}</span>
            </div>
            <div className="screenshot-info-row">
              <span className="screenshot-info-label">Distraction Type:</span>
              <span className="screenshot-info-val">
                {selected.faceFocus < 40 && selected.screenFocus < 40 ? '🔴 Both (Face + Screen)' :
                 selected.faceFocus < 40 ? '🟡 Face Disengagement' :
                 selected.screenFocus < 40 ? '🔵 Wrong App' : '✅ Focused'}
              </span>
            </div>
            <div className="screenshot-info-row">
              <span className="screenshot-info-label">Reason:</span>
              <span className="screenshot-info-val">{selected.reason}</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="screenshots-shell fade-in">
      <div className="screenshots-header">
        <div>
          <h3 className="screenshots-title">📸 Captured Moments</h3>
          <p className="screenshots-subtitle">{screenshots.length} screenshot{screenshots.length !== 1 ? 's' : ''} captured</p>
        </div>
        <button className="btn-sm btn-danger" onClick={clearAll}>🗑 Clear All</button>
      </div>

      <div className="screenshots-grid">
        {screenshots.map(s => (
          <div key={s.id} className="screenshot-card" onClick={() => setSelected(s)}>
            <div className="screenshot-image-wrap">
              <img src={s.screenImage} alt="Screenshot" className="screenshot-image" />
              <div className="screenshot-overlay">
                <span className="screenshot-type-badge">
                  {s.type === 'distraction' ? '🚨 Distracted' : '😰 Stressed'}
                </span>
              </div>
            </div>
            <div className="screenshot-info">
              <div className="screenshot-time">{new Date(s.timestamp).toLocaleTimeString()}</div>
              <div className="screenshot-scores">
                <span className="screenshot-score" style={{ color: s.focusScore < 30 ? '#DC2626' : '#F59E0B' }}>
                  Focus: {s.focusScore}%
                </span>
                <span className="screenshot-score" style={{ color: s.stressLevel > 70 ? '#DC2626' : '#F59E0B' }}>
                  Stress: {s.stressLevel}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
