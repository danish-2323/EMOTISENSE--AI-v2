import { Activity, BarChart2, BookOpen, Camera, Clock, FileText, History, Info, Power, Square, List } from 'lucide-react'

const NAV_STUDY = [
  { id: 'planner',      label: 'Plan Session',   icon: BookOpen },
  { id: 'focus',        label: 'Focus Monitor',  icon: Activity },
  { id: 'study-report', label: 'Study Report',   icon: FileText },
  { id: 'activity-log', label: 'Activity Log',   icon: List },
  { id: 'screenshots',  label: 'Screenshots',    icon: Camera },
  { id: 'history',      label: 'History',        icon: History },
]

const NAV_ADVANCED = [
  { id: 'dashboard',  label: 'Raw Monitor',    icon: Activity },
  { id: 'analytics',  label: 'Analytics',      icon: BarChart2 },
  { id: 'about',      label: 'About',          icon: Info },
]

export default function Sidebar({ page, setPage, sessionActive, simulation, onSimToggle, onStart, onStop, status }) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <h1>EMOTISENSE</h1>
        <span>Smart Study Analyser · v3.1</span>
      </div>

      {/* Navigation */}
      <nav className="nav-section">
        <p className="nav-label">Study</p>
        {NAV_STUDY.map(({ id, label, icon: Icon }) => (
          <button key={id} className={`nav-item ${page === id ? 'active' : ''}`} onClick={() => setPage(id)}>
            <Icon size={14} /> {label}
          </button>
        ))}
        <p className="nav-label" style={{ marginTop: 12 }}>Advanced</p>
        {NAV_ADVANCED.map(({ id, label, icon: Icon }) => (
          <button key={id} className={`nav-item ${page === id ? 'active' : ''}`} onClick={() => setPage(id)}>
            <Icon size={14} /> {label}
          </button>
        ))}
      </nav>

      {/* Session Controls */}
      <div className="controls-section">
        <p className="nav-label" style={{ padding: 0, marginBottom: 10 }}>Session</p>

        <label className="toggle-row" style={{ marginBottom: 8 }}>
          <span>Simulation mode</span>
          <label className="toggle">
            <input type="checkbox" checked={simulation} onChange={e => onSimToggle(e.target.checked)} disabled={sessionActive} />
            <span className="toggle-track" />
          </label>
        </label>

        {!sessionActive ? (
          <button className="btn btn-primary" onClick={onStart}>
            <Power size={14} /> Start Session
          </button>
        ) : (
          <button className="btn btn-danger" onClick={onStop}>
            <Square size={14} /> Stop Session
          </button>
        )}
      </div>

      {/* System status */}
      <div className="status-section">
        <p className="nav-label" style={{ marginBottom: 8 }}>System</p>
        <StatusRow label="Camera"      ok={status.camera} />
        <StatusRow label="Microphone"  ok={status.mic} />
        <StatusRow label="FER Model"   ok={status.fer} />
        <StatusRow label="Backend"     ok={status.backend} />
      </div>
    </aside>
  )
}

function StatusRow({ label, ok }) {
  return (
    <div className="status-row">
      <span className={`dot ${ok ? 'green' : 'red'}`} />
      <span>{label}</span>
      <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
        {ok ? 'OK' : 'OFF'}
      </span>
    </div>
  )
}