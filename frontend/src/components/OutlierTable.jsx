import { useMemo } from 'react'

export default function OutlierTable({
  page,
  total,
  limit,
  offset,
  onPage,
  onSelect,
  selected,
  knownOnly,
  onKnownOnlyChange,
}) {
  const rows = page?.outliers || []

  const maxPage = useMemo(() => Math.max(0, Math.ceil((total || 0) / limit) - 1), [total, limit])
  const pageIndex = limit > 0 ? Math.floor(offset / limit) : 0

  return (
    <div className="overflow-hidden rounded-xl border border-neon-magenta/20 bg-black/80 shadow-inner shadow-black/40 backdrop-blur-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-neon-magenta/15 px-4 py-3">
        <h2 className="font-display text-sm font-semibold text-zinc-100">Outlier events</h2>
        <label className="flex cursor-pointer items-center gap-2 text-xs text-zinc-400">
          <input
            type="checkbox"
            checked={knownOnly}
            onChange={(e) => onKnownOnlyChange(e.target.checked)}
            className="rounded border-zinc-600 bg-charcoal text-neon-magenta focus:ring-neon-magenta/50"
          />
          Known particles only
        </label>
      </div>
      <div className="max-h-[420px] overflow-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="sticky top-0 bg-charcoal/98 text-xs uppercase text-zinc-500 backdrop-blur">
            <tr>
              <th className="px-3 py-2">Run</th>
              <th className="px-3 py-2">Event</th>
              <th className="px-3 py-2">E1</th>
              <th className="px-3 py-2">E2</th>
              <th className="px-3 py-2">M</th>
              <th className="px-3 py-2">Particle</th>
              <th className="px-3 py-2">⟨ZZZ⟩</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((o) => {
              const sel =
                selected &&
                selected.run === o.run &&
                selected.event === o.event
              return (
                <tr
                  key={`${o.run}-${o.event}`}
                  onClick={() => onSelect(o)}
                  className={`cursor-pointer border-t border-zinc-800/90 hover:bg-neon-magenta/10 ${
                    sel ? 'bg-neon-magenta/15' : ''
                  }`}
                >
                  <td className="px-3 py-2 font-mono text-xs text-zinc-400">{o.run}</td>
                  <td className="px-3 py-2 font-mono text-xs text-zinc-400">{o.event}</td>
                  <td className="px-3 py-2 text-zinc-200">{o.E1?.toFixed(2)}</td>
                  <td className="px-3 py-2 text-zinc-200">{o.E2?.toFixed(2)}</td>
                  <td className="px-3 py-2 font-medium text-white">{o.M?.toFixed(3)}</td>
                  <td className="px-3 py-2">
                    <span
                      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                      style={{
                        backgroundColor: `${o.particle?.color || '#64748b'}22`,
                        color: o.particle?.color || '#e4e4e7',
                      }}
                    >
                      {o.particle?.symbol || '?'}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-amber-300">
                    {o.quantum_score != null ? o.quantum_score.toFixed(4) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-neon-magenta/15 px-4 py-2 text-xs text-zinc-500">
        <span>
          {total} rows · page {maxPage >= 0 ? pageIndex + 1 : 0} / {Math.max(1, maxPage + 1)}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={offset <= 0}
            className="rounded-lg border border-zinc-600 px-3 py-1 text-zinc-300 hover:border-neon-magenta/40 hover:bg-charcoal disabled:opacity-40"
            onClick={() => onPage(Math.max(0, offset - limit))}
          >
            Prev
          </button>
          <button
            type="button"
            disabled={offset + limit >= total}
            className="rounded-lg border border-zinc-600 px-3 py-1 text-zinc-300 hover:border-neon-magenta/40 hover:bg-charcoal disabled:opacity-40"
            onClick={() => onPage(offset + limit)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
