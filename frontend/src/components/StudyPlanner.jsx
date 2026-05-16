import { useState } from 'react'

const MODES   = ['Deep Focus', 'Light Review', 'Problem Solving', 'Reading']
const BREAKS  = ['Pomodoro 25/5', '50/10', 'Custom', 'None']
const DURATIONS = ['25 min', '45 min', '1 hr', 'Custom']

export default function StudyPlanner({ onStart }) {
  const [form, setForm] = useState({
    subject: '', duration: '45 min', customDuration: '',
    mode: 'Deep Focus', breakPref: 'Pomodoro 25/5', goals: '',
  })

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  function handleSubmit(e) {
    e.preventDefault()
    const mins =
      form.duration === 'Custom' ? parseInt(form.customDuration) || 45
      : form.duration === '25 min' ? 25
      : form.duration === '45 min' ? 45
      : 60
    const plan = { ...form, durationMins: mins, startedAt: Date.now() }
    localStorage.setItem('emotisense_current_plan', JSON.stringify(plan))
    onStart(plan)
  }

  return (
    <div className="planner-wrap fade-in">
      <div className="planner-card">
        <div className="planner-header">
          <h2 className="planner-title">📚 Plan Your Study Session</h2>
          <p className="planner-sub">Set clear goals and preferences to maximize your focus and productivity.</p>
        </div>

        <form onSubmit={handleSubmit} className="planner-form">
          <label className="planner-label">
            📝 Subject / Topic
            <input
              className="planner-input"
              placeholder="e.g. Calculus — Integration by Parts"
              value={form.subject}
              onChange={e => set('subject', e.target.value)}
              required
            />
          </label>

          <div className="planner-row">
            <label className="planner-label">
              ⏱ Target Duration
              <select className="planner-select" value={form.duration} onChange={e => set('duration', e.target.value)}>
                {DURATIONS.map(d => <option key={d}>{d}</option>)}
              </select>
            </label>
            {form.duration === 'Custom' && (
              <label className="planner-label">
                Minutes
                <input
                  className="planner-input"
                  type="number" min="5" max="300"
                  placeholder="e.g. 90"
                  value={form.customDuration}
                  onChange={e => set('customDuration', e.target.value)}
                />
              </label>
            )}
          </div>

          <div className="planner-row">
            <label className="planner-label">
              🎯 Study Mode
              <select className="planner-select" value={form.mode} onChange={e => set('mode', e.target.value)}>
                {MODES.map(m => <option key={m}>{m}</option>)}
              </select>
            </label>
            <label className="planner-label">
              ☕ Break Preference
              <select className="planner-select" value={form.breakPref} onChange={e => set('breakPref', e.target.value)}>
                {BREAKS.map(b => <option key={b}>{b}</option>)}
              </select>
            </label>
          </div>

          <label className="planner-label">
            🎯 Session Goals
            <textarea
              className="planner-textarea"
              placeholder="What do you want to achieve in this session? Be specific!"
              rows={3}
              value={form.goals}
              onChange={e => set('goals', e.target.value)}
            />
          </label>

          <div className="planner-tips">
            <span className="planner-tips-title">💡 Tips for Success:</span>
            <ul>
              <li>Set realistic, achievable goals</li>
              <li>Choose a distraction-free environment</li>
              <li>Share your entire screen for accurate tracking</li>
            </ul>
          </div>

          <button type="submit" className="btn-start-session">
            🚀 Start Focused Session
          </button>
        </form>
      </div>
    </div>
  )
}
