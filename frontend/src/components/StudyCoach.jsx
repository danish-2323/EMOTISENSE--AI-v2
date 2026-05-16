import { useState, useEffect, useRef } from 'react'

export default function StudyCoach({ sessionActive, liveData, plan }) {
  const [messages, setMessages] = useState([
    { role: 'coach', text: `👋 Ready to help you focus on "${plan?.subject || 'your session'}". Let's go!` }
  ])
  const [loading,  setLoading]  = useState(false)
  const bottomRef  = useRef(null)
  const lastNudge  = useRef(0)

  // Auto-nudge every 3 minutes if distracted
  useEffect(() => {
    if (!sessionActive || !liveData) return
    const now = Date.now()
    const stress = liveData.fused?.stress ?? 0
    const state  = liveData.study_state ?? ''
    if ((stress > 0.65 || state === 'Distracted') && now - lastNudge.current > 180_000) {
      lastNudge.current = now
      fetchNudge()
    }
  }, [liveData, sessionActive])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function fetchNudge() {
    setLoading(true)
    try {
      const res  = await fetch(`http://localhost:8000/study/coach/nudge?subject=${encodeURIComponent(plan?.subject || '')}&state=${encodeURIComponent(liveData?.study_state || 'Distracted')}`)
      const data = await res.json()
      push('coach', data.message)
    } catch {
      push('coach', '💡 Stay focused — you\'re doing great!')
    } finally { setLoading(false) }
  }

  function push(role, text) {
    setMessages(m => [...m, { role, text, ts: new Date().toLocaleTimeString() }])
  }

  return (
    <div className="coach-card">
      <div className="coach-header">
        <span className="coach-title">🤖 AI Study Coach</span>
        <button className="btn-sm btn-ghost" onClick={fetchNudge} disabled={loading || !sessionActive} title="Get coaching tip">
          {loading ? '⏳' : '💡'}
        </button>
      </div>
      <div className="coach-messages">
        {messages.map((m, i) => (
          <div key={i} className={`coach-msg coach-msg-${m.role}`}>
            <div className="coach-msg-bubble">
              <span className="coach-msg-text">{m.text}</span>
            </div>
            {m.ts && <span className="coach-msg-ts">{m.ts}</span>}
          </div>
        ))}
        {loading && (
          <div className="coach-msg coach-msg-coach">
            <div className="coach-msg-bubble">
              <span className="coach-typing">●●●</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
