import { useState, useEffect } from 'react'

export default function ActivityLog() {
  const [activities, setActivities] = useState([])
  const [filter, setFilter] = useState('all') // all, app-change, distraction, screenshot

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem('emotisense_activity_log') || '[]')
    setActivities(stored)
  }, [])

  const filtered = activities.filter(a => {
    if (filter === 'all') return true
    return a.type === filter
  })

  const getIcon = (type) => {
    switch(type) {
      case 'app-change': return '🔄'
      case 'distraction': return '⚠️'
      case 'screenshot': return '📸'
      case 'session-start': return '▶️'
      case 'session-end': return '⏹️'
      default: return '•'
    }
  }

  const getColor = (type) => {
    switch(type) {
      case 'app-change': return '#3b82f6'
      case 'distraction': return '#ef4444'
      case 'screenshot': return '#f59e0b'
      case 'session-start': return '#22c55e'
      case 'session-end': return '#6b7280'
      default: return '#6b7280'
    }
  }

  return (
    <div className="activity-log-page fade-in">
      <div className="activity-header">
        <div>
          <h2 className="activity-title">📋 Activity Log</h2>
          <p className="activity-subtitle">Detailed timeline of your study session</p>
        </div>
        
        <div className="activity-filters">
          <button 
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({activities.length})
          </button>
          <button 
            className={`filter-btn ${filter === 'app-change' ? 'active' : ''}`}
            onClick={() => setFilter('app-change')}
          >
            🔄 App Changes ({activities.filter(a => a.type === 'app-change').length})
          </button>
          <button 
            className={`filter-btn ${filter === 'distraction' ? 'active' : ''}`}
            onClick={() => setFilter('distraction')}
          >
            ⚠️ Distractions ({activities.filter(a => a.type === 'distraction').length})
          </button>
          <button 
            className={`filter-btn ${filter === 'screenshot' ? 'active' : ''}`}
            onClick={() => setFilter('screenshot')}
          >
            📸 Screenshots ({activities.filter(a => a.type === 'screenshot').length})
          </button>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="idle-overlay">
          <h3>No activities yet</h3>
          <p>Start a study session to see your activity timeline.</p>
        </div>
      ) : (
        <div className="activity-timeline">
          {filtered.map((activity, i) => (
            <div key={i} className="activity-item" style={{ borderLeftColor: getColor(activity.type) }}>
              <div className="activity-icon" style={{ background: getColor(activity.type) }}>
                {getIcon(activity.type)}
              </div>
              
              <div className="activity-content">
                <div className="activity-header-row">
                  <span className="activity-type">{activity.type.replace('-', ' ').toUpperCase()}</span>
                  <span className="activity-time">{new Date(activity.timestamp).toLocaleTimeString()}</span>
                </div>
                
                <div className="activity-details">
                  {activity.type === 'app-change' && (
                    <>
                      <div className="activity-detail-row">
                        <span className="detail-label">Expected App:</span>
                        <span className="detail-value">{activity.expectedApp}</span>
                      </div>
                      <div className="activity-detail-row">
                        <span className="detail-label">Detected App:</span>
                        <span className="detail-value" style={{ color: activity.isCorrectApp ? '#22c55e' : '#ef4444' }}>
                          {activity.detectedApp}
                        </span>
                      </div>
                      <div className="activity-detail-row">
                        <span className="detail-label">Focus Score:</span>
                        <span className="detail-value">{activity.focusScore}%</span>
                      </div>
                    </>
                  )}
                  
                  {activity.type === 'distraction' && (
                    <>
                      <div className="activity-detail-row">
                        <span className="detail-label">Reason:</span>
                        <span className="detail-value">{activity.reason}</span>
                      </div>
                      <div className="activity-detail-row">
                        <span className="detail-label">Expected App:</span>
                        <span className="detail-value">{activity.expectedApp}</span>
                      </div>
                      <div className="activity-detail-row">
                        <span className="detail-label">Current App:</span>
                        <span className="detail-value" style={{ color: '#ef4444' }}>{activity.currentApp}</span>
                      </div>
                      <div className="activity-metrics">
                        <span className="metric-badge">Face: {activity.faceFocus}%</span>
                        <span className="metric-badge">Screen: {activity.screenFocus}%</span>
                        <span className="metric-badge">Stress: {activity.stress}%</span>
                      </div>
                    </>
                  )}
                  
                  {activity.type === 'screenshot' && (
                    <>
                      <div className="activity-detail-row">
                        <span className="detail-label">Trigger:</span>
                        <span className="detail-value">{activity.trigger}</span>
                      </div>
                      <div className="activity-detail-row">
                        <span className="detail-label">App at Time:</span>
                        <span className="detail-value">{activity.detectedApp}</span>
                      </div>
                      <div className="activity-metrics">
                        <span className="metric-badge">Face: {activity.faceFocus}%</span>
                        <span className="metric-badge">Screen: {activity.screenFocus}%</span>
                        <span className="metric-badge">Stress: {activity.stress}%</span>
                      </div>
                    </>
                  )}
                  
                  {(activity.type === 'session-start' || activity.type === 'session-end') && (
                    <div className="activity-detail-row">
                      <span className="detail-label">Subject:</span>
                      <span className="detail-value">{activity.subject}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
