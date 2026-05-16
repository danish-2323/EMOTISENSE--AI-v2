import { useState, useEffect, useRef, useCallback } from 'react'
import Sidebar         from './components/Sidebar'
import Dashboard       from './components/Dashboard'
import SessionReport   from './components/SessionReport'
import StudyPlanner    from './components/StudyPlanner'
import FocusDashboard  from './components/FocusDashboard'
import StudyReport     from './components/StudyReport'
import SessionHistory  from './components/SessionHistory'
import Screenshots     from './components/Screenshots'
import ActivityLog     from './components/ActivityLog'

const WS_URL = 'ws://localhost:8000/ws/stream'
const MAX_HISTORY = 60   // keep last 60 seconds

export default function App() {
  const [page,          setPage]          = useState('planner')
  const [sessionActive, setSessionActive] = useState(false)
  const [simulation,    setSimulation]    = useState(false)
  const [liveData,      setLiveData]      = useState(null)
  const [history,       setHistory]       = useState([])
  const [sessionStats,  setSessionStats]  = useState(null)
  const [backendOk,     setBackendOk]     = useState(false)
  const [studyPlan,     setStudyPlan]     = useState(null)
  const [sessionStart,  setSessionStart]  = useState(null)  // timestamp when session started
  const [screenStream,  setScreenStream]  = useState(null)  // persistent screen share stream
  const [redirectTimer, setRedirectTimer] = useState(null)  // countdown for auto-redirect

  const wsRef = useRef(null)
  const pageBeforeSession = useRef('planner')  // track page before session started

  // Auto-redirect to focus page if session is active and user navigates away
  useEffect(() => {
    if (sessionActive && page !== 'focus' && page !== 'study-report') {
      setRedirectTimer(3)
      const countdown = setInterval(() => {
        setRedirectTimer(prev => {
          if (prev <= 1) {
            clearInterval(countdown)
            setPage('focus')
            return null
          }
          return prev - 1
        })
      }, 1000)
      return () => {
        clearInterval(countdown)
        setRedirectTimer(null)
      }
    } else {
      setRedirectTimer(null)
    }
  }, [page, sessionActive])

  // ── WebSocket connection ─────────────────────────────────────────────────
  const connectWS = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen    = ()  => { setBackendOk(true) }
    ws.onclose   = ()  => { setBackendOk(false); setTimeout(connectWS, 3000) }
    ws.onerror   = ()  => { setBackendOk(false) }

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.status === 'idle') return   // heartbeat
        setLiveData(msg)
        setHistory(prev => {
          const next = [...prev, msg]
          return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next
        })
      } catch (_) {}
    }
  }, [])

  useEffect(() => {
    connectWS()
    return () => wsRef.current?.close()
  }, [connectWS])

  // ── Session controls ─────────────────────────────────────────────────────
  async function handleStart(plan) {
    if (plan) setStudyPlan(plan)
    try {
      const res = await fetch('https://emotisence.netlify.app/session/start', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ simulation, plan: plan || studyPlan }),
      })
      const json = await res.json()
      if (json.ok) {
        pageBeforeSession.current = page
        setSessionActive(true)
        setSessionStart(Date.now())
        setHistory([])
        setLiveData(null)
        setSessionStats(null)
        setPage('focus')
        
        // Log session start
        const log = JSON.parse(localStorage.getItem('emotisense_activity_log') || '[]')
        log.push({
          type: 'session-start',
          timestamp: new Date().toISOString(),
          subject: (plan || studyPlan)?.subject || 'Unknown',
          duration: (plan || studyPlan)?.duration || '—'
        })
        localStorage.setItem('emotisense_activity_log', JSON.stringify(log))
      }
    } catch (e) {
      alert('Could not reach backend — is the FastAPI server running?\n\nuvicorn backend.server:app --reload --port 8000')
    }
  }

  async function handleStop() {
    try {
      const res  = await fetch('http://localhost:8000/session/stop', { method: 'POST' })
      const json = await res.json()
      if (json.ok) {
        setSessionActive(false)
        setSessionStart(null)
        setSessionStats(json.stats)
        setPage('study-report')
        // Stop screen share
        if (screenStream) {
          screenStream.getTracks().forEach(t => t.stop())
          setScreenStream(null)
        }
        
        // Log session end
        const log = JSON.parse(localStorage.getItem('emotisense_activity_log') || '[]')
        log.push({
          type: 'session-end',
          timestamp: new Date().toISOString(),
          subject: studyPlan?.subject || 'Unknown',
          duration: json.stats?.duration || '—'
        })
        localStorage.setItem('emotisense_activity_log', JSON.stringify(log))
      }
    } catch (e) {
      setSessionActive(false)
    }
  }

  // ── System status (derived) ───────────────────────────────────────────────
  const status = {
    backend: backendOk,
    camera:  sessionActive && !simulation && !!liveData?.frame,
    mic:     sessionActive,
    fer:     sessionActive && !!liveData?.face && Object.keys(liveData.face).length > 0,
  }

  // ── Render ────────────────────────────────────────────────────────────────
  const PAGE_TITLES = {
    planner:       'Plan Session',
    focus:         'Focus Monitor',
    'study-report':'Study Report',
    'activity-log':'Activity Log',
    history:       'Session History',
    screenshots:   'Screenshots',
    dashboard:     'Raw Emotion Monitor',
    report:        'Raw Session Data',
    analytics:     'Analytics',
    about:         'About',
  }

  return (
    <div className="app-shell">
      <Sidebar
        page={page}
        setPage={setPage}
        sessionActive={sessionActive}
        simulation={simulation}
        onSimToggle={setSimulation}
        onStart={() => handleStart()}
        onStop={handleStop}
        status={status}
      />

      <main className="main">
        {redirectTimer && (
          <div className="redirect-banner">
            ⏱ Session active — returning to Focus Monitor in {redirectTimer}s...
            <button className="btn-sm btn-ghost" onClick={() => setPage('focus')}>Go Now</button>
          </div>
        )}

        <div className="page-header">
          <h2 className="page-title">{PAGE_TITLES[page] ?? page}</h2>
          <span className="page-sub">EMOTISENSE AI · Smart Study Analyser</span>
        </div>

        {page === 'planner' && (
          <StudyPlanner onStart={handleStart} />
        )}

        {page === 'focus' && (
          <FocusDashboard
            data={liveData}
            history={history}
            sessionActive={sessionActive}
            plan={studyPlan}
            sessionStart={sessionStart}
            screenStream={screenStream}
            setScreenStream={setScreenStream}
          />
        )}

        {page === 'study-report' && (
          <StudyReport stats={sessionStats} history={history} plan={studyPlan} />
        )}

        {page === 'activity-log' && <ActivityLog />}

        {page === 'history' && <SessionHistory />}

        {page === 'screenshots' && <Screenshots />}

        {page === 'dashboard' && (
          <Dashboard data={liveData} history={history} sessionActive={sessionActive} />
        )}

        {page === 'report' && (
          <SessionReport stats={sessionStats} history={history} />
        )}

        {page === 'analytics' && (
          <AnalyticsPlaceholder history={history} />
        )}

        {page === 'about' && <AboutPage />}
      </main>
    </div>
  )
}

// ── Simple analytics placeholder ─────────────────────────────────────────────
function AnalyticsPlaceholder({ history }) {
  if (history.length < 5) {
    return (
      <div className="idle-overlay fade-in">
        <h3>Not enough data</h3>
        <p>Run a session for at least 30 seconds to see analytics.</p>
      </div>
    )
  }

  // Peak stress moment
  const peak     = history.reduce((a,b) => (b.fused?.stress ?? 0) > (a.fused?.stress ?? 0) ? b : a, history[0])
  const avgStr   = (history.reduce((s,d) => s + (d.fused?.stress ?? 0), 0) / history.length * 100).toFixed(1)
  const avgEng   = (history.reduce((s,d) => s + (d.fused?.engagement ?? 0), 0) / history.length * 100).toFixed(1)

  const quality =
    avgStr < 30 && avgEng > 55 ? { grade: 'Excellent', color: '#16A34A' }
    : avgStr < 50 ? { grade: 'Good',   color: '#1D4ED8' }
    : avgStr < 70 ? { grade: 'Fair',   color: '#D97706' }
    : { grade: 'Needs Attention', color: '#DC2626' }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }} className="fade-in">
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Avg Stress</span>
          <span className="metric-value">{avgStr}<small style={{ fontSize: 16, color: 'var(--text-muted)' }}>%</small></span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Avg Engagement</span>
          <span className="metric-value">{avgEng}<small style={{ fontSize: 16, color: 'var(--text-muted)' }}>%</small></span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Session Quality</span>
          <span className="metric-value" style={{ fontSize: 22, color: quality.color }}>{quality.grade}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Data Points</span>
          <span className="metric-value">{history.length}</span>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Insight</span></div>
        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
          {avgStr < 35
            ? <p>✅ Stress levels were consistently low — the session was calm and manageable.</p>
            : avgStr < 60
            ? <p>⚠️ Moderate stress levels detected. Consider shorter sessions or more breaks.</p>
            : <p>🔴 High sustained stress detected. Significant emotional load during this session.</p>
          }
          {avgEng > 55
            ? <p>✅ Engagement was strong throughout — attention remained high.</p>
            : <p>⚠️ Engagement dipped during parts of the session. Consider identifying distraction triggers.</p>
          }
          <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>
            Peak stress of {Math.round((peak.fused?.stress ?? 0) * 100)}% detected at second {history.indexOf(peak)}.
          </p>
        </div>
      </div>
    </div>
  )
}

// ── About page ────────────────────────────────────────────────────────────────
function AboutPage() {
  return (
    <div className="card fade-in" style={{ maxWidth: 640 }}>
      <div className="card-header"><span className="card-title">About EMOTISENSE AI</span></div>
      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 16, fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
        <p>EMOTISENSE AI is a real-time multimodal emotion monitoring system that combines facial emotion detection and audio stress analysis to provide comprehensive emotional insights during sessions.</p>
        <div>
          <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>Technology Stack</p>
          <ul style={{ paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 4 }}>
            <li>Computer Vision — OpenCV, FER, MediaPipe</li>
            <li>Audio Analysis — librosa, sounddevice</li>
            <li>Backend — FastAPI, WebSockets</li>
            <li>Frontend — React 18, Recharts, Vite</li>
            <li>Reports — ReportLab PDF generation</li>
          </ul>
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          Built by Team PRIMELOGIX · B.Tech AI &amp; Data Science · SRM IST × NOOBTRON Hackfest
        </p>
      </div>
    </div>
  )
}
