export default function StatsPanel({ stats }) {
  if (!stats) return null
  const rows = ['E1', 'E2', 'M']
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {rows.map((k) => (
        <div
          key={k}
          className="rounded-xl border border-neon-green/20 bg-black/80 p-4 shadow-lg shadow-black/30 backdrop-blur-sm"
        >
          <p className="font-display text-xs font-semibold uppercase tracking-wider text-zinc-500">
            {k}
          </p>
          <dl className="mt-3 space-y-1 text-sm text-zinc-300">
            <div className="flex justify-between gap-2">
              <dt className="text-zinc-500">μ</dt>
              <dd className="text-zinc-100">{stats.z[k]?.mean?.toFixed(3)}</dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className="text-zinc-500">σ</dt>
              <dd className="text-zinc-100">{stats.z[k]?.std?.toFixed(3)}</dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className="text-zinc-500">min–max</dt>
              <dd className="text-right text-xs text-zinc-200">
                {stats.min[k]?.toFixed(1)} … {stats.max[k]?.toFixed(1)}
              </dd>
            </div>
          </dl>
        </div>
      ))}
    </div>
  )
}
