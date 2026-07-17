/** Classical vs quantum probability comparison for verification phase. */

function pct(value) {
  if (value == null || Number.isNaN(value)) return '—'
  return `${(value * 100).toFixed(2)}%`
}

function Bar({ label, value, max, color }) {
  const width = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-zinc-500">{label}</span>
        <span className="font-mono text-zinc-300">{pct(value)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-zinc-900">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{ width: `${width}%`, backgroundColor: color }}
        />
      </div>
    </div>
  )
}

export default function GroundTruthValidation({ classical, quantum }) {
  const exact = classical?.exact_classical_probability ?? quantum?.exact_classical_probability
  const binned =
    classical?.binned_classical_probability ?? quantum?.binned_classical_probability
  const estimate = quantum?.estimate
  const stderr = quantum?.standard_error
  const verification = quantum?.verification

  const values = [exact, binned, estimate].filter((v) => typeof v === 'number')
  const max = values.length ? Math.max(...values, 0.001) : 0.001

  const disc =
    classical?.discretization_error ??
    (typeof binned === 'number' && typeof exact === 'number' ? binned - exact : null)

  return (
    <div className="mt-3 space-y-3 rounded-lg border border-cyan-500/20 bg-zinc-950/90 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-cyan-200/90">
          Ground truth verification
        </h4>
        {verification?.within_2sigma_of_exact != null && (
          <span
            className={`rounded px-2 py-0.5 text-xs font-medium ${
              verification.within_2sigma_of_exact
                ? 'bg-emerald-500/20 text-emerald-300'
                : 'bg-amber-500/20 text-amber-200'
            }`}
          >
            {verification.within_2sigma_of_exact ? 'Within 2σ of exact' : 'Outside 2σ of exact'}
          </span>
        )}
      </div>

      <div className="space-y-2">
        <Bar label="Exact classical P(window)" value={exact} max={max} color="#22d3ee" />
        <Bar label="Binned classical P(window)" value={binned} max={max} color="#a78bfa" />
        {estimate != null && (
          <Bar label="Quantum sample P(window)" value={estimate} max={max} color="#fbbf24" />
        )}
      </div>

      <dl className="grid gap-2 text-xs sm:grid-cols-2">
        <div>
          <dt className="text-zinc-500">Discretization (binned − exact)</dt>
          <dd className="font-mono text-zinc-200">
            {disc != null ? `${disc >= 0 ? '+' : ''}${(disc * 100).toFixed(3)} pp` : '—'}
          </dd>
        </div>
        {verification?.quantum_vs_exact != null && (
          <div>
            <dt className="text-zinc-500">Quantum − exact</dt>
            <dd className="font-mono text-zinc-200">
              {(verification.quantum_vs_exact * 100).toFixed(3)} pp
              {stderr != null && (
                <span className="text-zinc-500">
                  {' '}
                  ({verification.quantum_vs_exact_sigma?.toFixed(1) ?? '—'}σ)
                </span>
              )}
            </dd>
          </div>
        )}
        {classical?.bin_count != null && (
          <div>
            <dt className="text-zinc-500">Mass bins (2ⁿ)</dt>
            <dd className="font-mono text-zinc-200">{classical.bin_count}</dd>
          </div>
        )}
        {classical?.event_count != null && (
          <div>
            <dt className="text-zinc-500">Events</dt>
            <dd className="font-mono text-zinc-200">{classical.event_count.toLocaleString()}</dd>
          </div>
        )}
      </dl>
    </div>
  )
}
