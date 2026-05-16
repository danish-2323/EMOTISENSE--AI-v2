/**
 * SVG semicircle arc gauge for stress.
 * Goes from blue (low) → amber (mid) → red (high).
 */
export default function StressGauge({ value = 0 }) {
  const pct     = Math.min(1, Math.max(0, value))
  const size    = 160
  const cx      = size / 2
  const cy      = size / 2 + 10
  const r       = 62
  const stroke  = 10
  const circum  = Math.PI * r          // half circle
  const filled  = circum * pct

  // Color interpolation: blue → amber → red
  const color = pct < 0.5
    ? lerpColor('#1D4ED8', '#D97706', pct * 2)
    : lerpColor('#D97706', '#DC2626', (pct - 0.5) * 2)

  const stateLabel =
    pct < 0.35 ? 'Calm'
    : pct < 0.65 ? 'Moderate'
    : pct < 0.85 ? 'Elevated'
    : 'High stress'

  return (
    <div className="gauge-wrap">
      <span className="gauge-label">Stress Level</span>
      <svg width={size} height={size / 2 + 20} viewBox={`0 0 ${size} ${size / 2 + 20}`}>
        {/* Track */}
        <path
          d={describeArc(cx, cy, r)}
          fill="none"
          stroke="var(--bg-alt)"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        {/* Fill */}
        <path
          d={describeArc(cx, cy, r)}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circum}`}
          style={{ transition: 'stroke-dasharray .6s cubic-bezier(.4,0,.2,1), stroke .4s' }}
        />
        {/* Value text */}
        <text
          x={cx} y={cy - 4}
          textAnchor="middle"
          fontFamily="var(--font-mono)"
          fontSize="22"
          fill="var(--text-primary)"
        >
          {Math.round(pct * 100)}%
        </text>
        <text
          x={cx} y={cy + 16}
          textAnchor="middle"
          fontFamily="var(--font-body)"
          fontSize="11"
          fill="var(--text-muted)"
          fontStyle="italic"
        >
          {stateLabel}
        </text>
        {/* Min / max labels */}
        <text x={cx - r - 4} y={cy + 6} textAnchor="end"
          fontFamily="var(--font-mono)" fontSize="9" fill="var(--text-muted)">0</text>
        <text x={cx + r + 4} y={cy + 6} textAnchor="start"
          fontFamily="var(--font-mono)" fontSize="9" fill="var(--text-muted)">100</text>
      </svg>
    </div>
  )
}

// ── helpers ──────────────────────────────────────────────────────────────────
function describeArc(cx, cy, r) {
  // Left to right semicircle (180° arc)
  const startX = cx - r
  const startY = cy
  const endX   = cx + r
  const endY   = cy
  return `M ${startX} ${startY} A ${r} ${r} 0 0 1 ${endX} ${endY}`
}

function lerpColor(a, b, t) {
  const ah = parseInt(a.slice(1), 16)
  const bh = parseInt(b.slice(1), 16)
  const ar = (ah >> 16) & 0xff, ag = (ah >> 8) & 0xff, ab = ah & 0xff
  const br = (bh >> 16) & 0xff, bg = (bh >> 8) & 0xff, bb = bh & 0xff
  const r  = Math.round(ar + (br - ar) * t)
  const g  = Math.round(ag + (bg - ag) * t)
  const blue = Math.round(ab + (bb - ab) * t)
  return `#${((1 << 24) | (r << 16) | (g << 8) | blue).toString(16).slice(1)}`
}