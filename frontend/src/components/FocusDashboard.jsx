import PomodoroTimer from './PomodoroTimer'
import ScreenShare   from './ScreenShare'
import StudyCoach    from './StudyCoach'
import { useState, useEffect }  from 'react'

const STATE_COLOR = {
  'Deep Focus':   '#22c55e',
  'Light Focus':  '#3b82f6',
  'Distracted':   '#f59e0b',
  'Fatigued':     '#a78bfa',
  'Stressed':     '#ef4444',
  'On Break':     '#06b6d4',
  'Idle':         '#6b7280',
}

export default function FocusDashboard({ data, history, sessionActive, plan, sessionStart, screenStream, setScreenStream }) {
  const [onBreak,      setOnBreak]      = useState(false)
  const [screenFocus,  setScreenFocus]  = useState(null)
  const [screenAlert,  setScreenAlert]  = useState(null)
  const [faceFrame,    setFaceFrame]    = useState(null)  // Current face frame for screenshots

  const fused      = data?.fused ?? {}
  const studyState = data?.study_state ?? (onBreak ? 'On Break' : 'Idle')
  const stateColor = STATE_COLOR[studyState] ?? '#6b7280'

  // Store latest face frame
  useEffect(() => {
    if (data?.frame) {
      setFaceFrame(data.frame)
    }
  }, [data?.frame])

  // Combined focus score: facial engagement (40%) + screen focus (60%)
  // Screen is weighted higher because it's more objective
  const faceFocus  = Math.round((fused.engagement ?? 0) * 100)
  const combined   = screenFocus !== null
    ? Math.round(faceFocus * 0.4 + screenFocus * 0.6)
    : faceFocus

  // Determine if truly focused (STRICT: both face AND screen must be good)
  const isTrulyFocused = faceFocus >= 65 && (screenFocus === null || screenFocus >= 80)
  const isDistracted   = faceFocus < 35 || (screenFocus !== null && screenFocus < 50)

  // Active vs distracted time
  const total      = history.length || 1
  const distracted = history.filter(d => ['Distracted','Idle'].includes(d.study_state)).length
  const activeTime = Math.round(((total - distracted) / total) * 100)

  // Session duration
  const elapsed = sessionStart ? Math.floor((Date.now() - sessionStart) / 1000) : 0
  const elapsedMin = Math.floor(elapsed / 60)
  const elapsedSec = elapsed % 60

  if (!sessionActive) {
    return (
      <div className="idle-overlay fade-in">
        <h3>No active session</h3>
        <p>Plan a session to start focus monitoring.</p>
      </div>
    )
  }

  return (
    <div className="focus-shell fade-in">

      {/* Top row — state + focus score */}
      <div className="focus-top-row">
        <div className="focus-state-card" style={{ borderColor: stateColor }}>
          <span className="focus-state-label">Attention State</span>
          <span className="focus-state-val" style={{ color: stateColor }}>{studyState}</span>
          <span className="focus-state-sub">{plan?.subject || 'Study Session'}</span>
        </div>

        <div className="focus-score-card">
          <span className="focus-score-label">Focus Score</span>
          <span className="focus-score-val" style={{ color: combined >= 80 ? '#22c55e' : combined >= 60 ? '#3b82f6' : combined >= 40 ? '#f59e0b' : '#ef4444' }}>
            {combined}<small>/100</small>
          </span>
          <div className="focus-score-breakdown">
            <span title="Facial engagement">Face: {faceFocus}%</span>
            {screenFocus !== null && <span title="On-task app usage">Screen: {screenFocus}%</span>}
          </div>
          <div className="focus-score-formula">
            {screenFocus !== null ? 'Face 40% + Screen 60%' : 'Face only'}
          </div>
        </div>

        <div className="focus-time-card">
          <span className="focus-time-label">Session Progress</span>
          <div className="focus-session-time">{elapsedMin}:{String(elapsedSec).padStart(2,'0')}</div>
          <div className="focus-time-bar-bg">
            <div className="focus-time-bar-fill" style={{ width: `${activeTime}%` }} />
          </div>
          <span className="focus-time-pct">Active: {activeTime}%</span>
        </div>
      </div>

      {/* Alert banner for combined distractions - MORE SENSITIVE */}
      {isDistracted && sessionActive && (
        <div className="focus-alert-banner focus-alert-critical">
          🚨 DISTRACTION DETECTED:
          {faceFocus < 35 && screenFocus !== null && screenFocus < 50 && ' Face disengaged + Wrong app'}
          {faceFocus < 35 && (screenFocus === null || screenFocus >= 50) && ' Face shows low engagement - look at screen!'}
          {faceFocus >= 35 && screenFocus !== null && screenFocus < 50 && ' You\'re in the wrong app - return to study material!'}
        </div>
      )}

      {/* Screen alert banner */}
      {screenAlert && (
        <div className="focus-alert-banner">⚠️ {screenAlert}</div>
      )}

      {/* Middle row — metrics */}
      <div className="focus-metrics-row">
        {[
          { label: 'Face Focus',  val: faceFocus,                                unit: '%', warn: v => v < 35, icon: '😊', desc: 'Facial engagement' },
          { label: 'Screen Focus', val: screenFocus ?? '—',                      unit: screenFocus ? '%' : '', warn: v => v !== '—' && v < 50, icon: '🖥', desc: 'On-task app usage' },
          { label: 'Stress',      val: Math.round((fused.stress      ?? 0) * 100), unit: '%', warn: v => v > 60, icon: '😰', desc: 'Stress level' },
          { label: 'Confidence',  val: Math.round((fused.confidence  ?? 0) * 100), unit: '%', warn: () => false, icon: '💪', desc: 'Confidence level' },
        ].map(m => (
          <div key={m.label} className="focus-metric-chip" title={m.desc}>
            <span className="fmc-icon">{m.icon}</span>
            <span className="fmc-label">{m.label}</span>
            <span className="fmc-val" style={{ color: m.warn(m.val) ? '#ef4444' : 'var(--text-primary)' }}>
              {m.val}{m.unit}
            </span>
          </div>
        ))}
      </div>

      {/* Bottom row — timer + screen + coach */}
      <div className="focus-bottom-row">
        <PomodoroTimer plan={plan} sessionStart={sessionStart} onBreakChange={setOnBreak} />
        <ScreenShare
          sessionActive={sessionActive}
          screenStream={screenStream}
          setScreenStream={setScreenStream}
          onFocusScore={(s, a) => { setScreenFocus(s); setScreenAlert(a) }}
          faceFrame={faceFrame}
          faceFocus={faceFocus}
          stress={Math.round((fused.stress ?? 0) * 100)}
        />
        <StudyCoach sessionActive={sessionActive} liveData={data} plan={plan} />
      </div>

    </div>
  )
}
