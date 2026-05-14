import { useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

function binOutliers(outliers, edges) {
  const counts = new Array(Math.max(0, edges.length - 1)).fill(0)
  if (!outliers?.length || edges.length < 2) return counts
  const last = edges.length - 2
  for (const o of outliers) {
    const m = o.M
    let idx = last
    for (let i = 0; i <= last; i++) {
      if (m >= edges[i] && m < edges[i + 1]) {
        idx = i
        break
      }
    }
    if (m >= edges[edges.length - 1]) idx = last
    counts[idx] += 1
  }
  return counts
}

const GRID_STROKE = '#3d4f3d'
const TICK_FILL = '#a1a1aa'
const AXIS_LABEL_FILL = '#71717a'
const BAR_FILL = '#6b21a8'
const OUTLIER_FILL = '#f43f5e'

export default function MassSpectrum({ spectrum, outliers, massRange, onBarClick }) {
  const chartData = useMemo(() => {
    if (!spectrum?.edges || !spectrum?.counts) return []
    const { edges, counts } = spectrum
    const out = binOutliers(outliers, edges)
    return counts.map((c, i) => ({
      lo: edges[i],
      hi: edges[i + 1],
      m: (edges[i] + edges[i + 1]) / 2,
      n: c,
      nOut: out[i] || 0,
    }))
  }, [spectrum, outliers])

  const [mMin, mMax] = massRange || [
    chartData[0]?.lo ?? 0,
    chartData[chartData.length - 1]?.hi ?? 120,
  ]

  const particlesInView = useMemo(() => {
    return (spectrum?.particles || []).filter((p) => p.mass >= mMin && p.mass <= mMax)
  }, [spectrum, mMin, mMax])

  return (
    <div className="h-[380px] w-full rounded-xl border border-neon-magenta/20 bg-black/80 p-2 shadow-inner shadow-black/40 backdrop-blur-sm">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} strokeWidth={1} />
          <XAxis
            dataKey="m"
            type="number"
            domain={[mMin, mMax]}
            tick={{ fill: TICK_FILL, fontSize: 11 }}
            label={{
              value: 'Invariant mass M (GeV)',
              position: 'insideBottom',
              offset: -2,
              fill: AXIS_LABEL_FILL,
            }}
          />
          <YAxis tick={{ fill: TICK_FILL, fontSize: 11 }} width={44} />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null
              const p = payload[0]?.payload
              if (!p) return null
              return (
                <div className="rounded-lg border border-neon-magenta/30 bg-charcoal px-3 py-2 text-xs text-zinc-100 shadow-xl">
                  <div className="font-medium text-white">M ≈ {Number(label).toFixed(3)} GeV</div>
                  <div className="mt-1 text-zinc-400">Events: {p.n}</div>
                  <div className="text-zinc-400">Outliers in bin: {p.nOut}</div>
                </div>
              )
            }}
          />
          {particlesInView.map((p) => (
            <ReferenceLine
              key={p.name}
              x={p.mass}
              stroke={p.color || '#64748b'}
              strokeDasharray="4 4"
              label={{ value: p.symbol, fill: p.color || '#e4e4e7', fontSize: 11, position: 'top' }}
            />
          ))}
          <Bar dataKey="n" radius={[2, 2, 0, 0]} onClick={(d) => onBarClick?.(d)}>
            {chartData.map((entry, i) => (
              <Cell
                key={i}
                cursor="pointer"
                fill={entry.nOut > 0 ? OUTLIER_FILL : BAR_FILL}
                fillOpacity={entry.nOut > 0 ? 0.95 : 0.92}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
