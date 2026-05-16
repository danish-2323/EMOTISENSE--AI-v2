import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend
} from 'recharts'

const LINES = [
  { key: 'stress',     color: '#DC2626', label: 'Stress' },
  { key: 'engagement', color: '#16A34A', label: 'Engagement' },
  { key: 'confidence', color: '#1D4ED8', label: 'Confidence' },
  { key: 'confusion',  color: '#D97706', label: 'Confusion' },
]

export default function TimelineChart({ history }) {
  if (!history || history.length < 2) {
    return (
      <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--text-muted)', fontSize: 13 }}>
        Waiting for data…
      </div>
    )
  }

  const data = history.map((d, i) => ({
    t:          i,
    stress:     +(d.fused?.stress     ?? 0).toFixed(3),
    engagement: +(d.fused?.engagement ?? 0).toFixed(3),
    confidence: +(d.fused?.confidence ?? 0).toFixed(3),
    confusion:  +(d.fused?.confusion  ?? 0).toFixed(3),
  }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
        <XAxis
          dataKey="t"
          tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--text-muted)' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={v => `${v}s`}
        />
        <YAxis
          domain={[0, 1]}
          tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--text-muted)' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={v => `${Math.round(v * 100)}%`}
        />
        <Tooltip
          contentStyle={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 8,
          }}
          formatter={(v, name) => [`${Math.round(v * 100)}%`, name]}
        />
        <Legend
          wrapperStyle={{ fontFamily: 'var(--font-body)', fontSize: 12, paddingTop: 8 }}
          iconType="circle"
          iconSize={8}
        />
        {LINES.map(({ key, color, label }) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={color}
            strokeWidth={2}
            dot={false}
            name={label}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}