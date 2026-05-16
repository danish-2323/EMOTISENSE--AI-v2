import { useState } from 'react'
import { Download, FileText, BarChart2 } from 'lucide-react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip
} from 'recharts'

export default function SessionReport({ stats, history }) {
  const [loading, setLoading] = useState(false)

  async function downloadCSV() {
    window.open('https://emotisense-e6z2.onrender.com/session/export/csv', '_blank')
  }

  async function downloadPDF() {
    setLoading(true)
    try {
      const res = await fetch('https://emotisense-e6z2.onrender.com/session/export/pdf', { method: 'POST' })
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = 'emotisense_report.pdf'; a.click()
    } catch (e) {
      alert('PDF generation failed — check backend logs.')
    } finally {
      setLoading(false)
    }
  }

  if (!stats || !stats.total_records) {
    return (
      <div className="idle-overlay fade-in">
        <BarChart2 size={40} strokeWidth={1} />
        <h3>No session data yet</h3>
        <p>Complete a session to view the full report, statistics, and export options.</p>
      </div>
    )
  }

  // Build chart data from history
  const chartData = history.map((d, i) => ({
    t:          i,
    stress:     +(d.fused?.stress     ?? 0).toFixed(3),
    engagement: +(d.fused?.engagement ?? 0).toFixed(3),
  }))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }} className="fade-in">

      {/* Stats grid */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Session Summary</span>
          <span className="timestamp">ID: {stats.session_id}</span>
        </div>
        <div className="card-body">
          <dl className="stats-grid">
            <StatBlock label="Duration"       value={stats.duration      ?? '—'} />
            <StatBlock label="Records"        value={stats.total_records ?? 0}   />
            <StatBlock label="Avg Stress"     value={`${Math.round((stats.avg_stress     ?? 0) * 100)}%`} />
            <StatBlock label="Avg Engagement" value={`${Math.round((stats.avg_engagement ?? 0) * 100)}%`} />
            <StatBlock label="Avg Confidence" value={`${Math.round((stats.avg_confidence ?? 0) * 100)}%`} />
            <StatBlock label="Peak Stress"    value={`${Math.round((stats.peak_stress    ?? 0) * 100)}%`} />
          </dl>
        </div>
      </div>

      {/* Session chart */}
      {chartData.length > 1 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Stress &amp; Engagement Over Session</span>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
                <defs>
                  <linearGradient id="gStress" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#DC2626" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#DC2626" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gEngage" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#16A34A" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#16A34A" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="t" tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--text-muted)' }}
                  tickLine={false} axisLine={false} tickFormatter={v => `${v}s`} />
                <YAxis domain={[0,1]} tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--text-muted)' }}
                  tickLine={false} axisLine={false} tickFormatter={v => `${Math.round(v*100)}%`} />
                <Tooltip contentStyle={{ fontFamily: 'var(--font-mono)', fontSize: 11,
                  background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8 }}
                  formatter={(v, n) => [`${Math.round(v*100)}%`, n]} />
                <Area type="monotone" dataKey="stress"     stroke="#DC2626" strokeWidth={2}
                  fill="url(#gStress)" dot={false} name="Stress" isAnimationActive={false} />
                <Area type="monotone" dataKey="engagement" stroke="#16A34A" strokeWidth={2}
                  fill="url(#gEngage)" dot={false} name="Engagement" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Dominant states */}
      {stats.dominant_states && Object.keys(stats.dominant_states).length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Dominant States Distribution</span>
          </div>
          <div className="card-body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {Object.entries(stats.dominant_states)
                .sort(([,a],[,b]) => b - a)
                .map(([state, count]) => {
                  const total = Object.values(stats.dominant_states).reduce((a,b) => a+b, 0)
                  const pct   = Math.round(count / total * 100)
                  return (
                    <div key={state} style={{ display: 'grid', gridTemplateColumns: '100px 1fr 44px', alignItems: 'center', gap: 10 }}>
                      <span className={`state-badge ${state}`} style={{ justifySelf: 'start' }}>{state}</span>
                      <div className="emotion-track" style={{ height: 6 }}>
                        <div className="emotion-fill" style={{ width: `${pct}%`, background: '#1D4ED8' }} />
                      </div>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', textAlign: 'right' }}>
                        {pct}%
                      </span>
                    </div>
                  )
                })
              }
            </div>
          </div>
        </div>
      )}

      {/* Export */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Export</span>
        </div>
        <div className="card-body">
          <div className="export-row">
            <button className="btn-outline" onClick={downloadCSV}>
              <Download size={14} /> Download CSV
            </button>
            <button className="btn-outline" onClick={downloadPDF} disabled={loading}>
              <FileText size={14} /> {loading ? 'Generating…' : 'Download PDF Report'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatBlock({ label, value }) {
  return (
    <div className="stat-block">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  )
}
