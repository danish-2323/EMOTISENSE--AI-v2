import { useState, useEffect, useRef } from 'react'

function parsePref(pref) {
  if (pref === 'Pomodoro 25/5') return { work: 25, brk: 5 }
  if (pref === '50/10')         return { work: 50, brk: 10 }
  if (pref === 'None')          return null
  return { work: 25, brk: 5 } // Custom default
}

export default function PomodoroTimer({ plan, sessionStart, onBreakChange }) {
  const cfg = parsePref(plan?.breakPref)
  const totalMins = plan?.durationMins || 45

  const [phase,    setPhase]    = useState('work')
  const [secs,     setSecs]     = useState((cfg?.work || totalMins) * 60)
  const [round,    setRound]    = useState(1)
  const [running,  setRunning]  = useState(true)
  const [now,      setNow]      = useState(Date.now())
  const intervalRef = useRef(null)

  // Calculate elapsed from sessionStart
  const elapsed = sessionStart ? Math.floor((now - sessionStart) / 1000) : 0

  useEffect(() => {
    if (!running) { clearInterval(intervalRef.current); return }
    intervalRef.current = setInterval(() => {
      setNow(Date.now())
      setSecs(s => {
        if (s <= 1) {
          if (!cfg) return 0
          const next = phase === 'work' ? 'break' : 'work'
          setPhase(next)
          onBreakChange?.(next === 'break')
          if (next === 'work') setRound(r => r + 1)
          return (next === 'break' ? cfg.brk : cfg.work) * 60
        }
        return s - 1
      })
    }, 1000)
    return () => clearInterval(intervalRef.current)
  }, [running, phase, cfg, onBreakChange])

  const fmt = s => `${String(Math.floor(s / 60)).padStart(2,'0')}:${String(s % 60).padStart(2,'0')}`
  const totalSecs = (phase === 'work' ? (cfg?.work || totalMins) : (cfg?.brk || 5)) * 60
  const pct = Math.round((1 - secs / totalSecs) * 100)

  return (
    <div className={`pomodoro-card ${phase === 'break' ? 'pomodoro-break' : ''}`}>
      <div className="pomodoro-header">
        <div className="pomodoro-phase">{phase === 'break' ? '☕ Break Time' : `🍅 Round ${round}`}</div>
        <button className="pomodoro-toggle" onClick={() => setRunning(r => !r)}>
          {running ? '⏸' : '▶'}
        </button>
      </div>
      <div className="pomodoro-time">{fmt(secs)}</div>
      <div className="pomodoro-bar-bg">
        <div className="pomodoro-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="pomodoro-footer">
        <span className="pomodoro-meta">⏱ Session: {fmt(elapsed)} / {fmt(totalMins * 60)}</span>
        <span className="pomodoro-progress">{pct}%</span>
      </div>
    </div>
  )
}
