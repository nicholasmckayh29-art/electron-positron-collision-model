/** Adaptive loop iterations, convergence status, and databank feedback. */

function pct(value) {
  if (value == null || Number.isNaN(value)) return '—'
  return `${(value * 100).toFixed(3)}%`
}

export default function AdaptiveConvergencePanel({ result }) {
  if (!result) return null

  const convergence = result.convergence || {}
  const iterations = result.iterations || []
  const isAdaptive = result.pipeline_mode === 'adaptive_snapshot'

  return (
    <div className="mt-3 space-y-3 rounded-lg border border-amber-400/20 bg-zinc-950/90 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-amber-200/90">
          {isAdaptive ? 'Adaptive control loop' : 'Job result'}
        </h4>
        {result.pipeline_mode && (
          <span className="rounded bg-zinc-800 px-2 py-0.5 font-mono text-[10px] text-zinc-300">
            {result.pipeline_mode}
          </span>
        )}
      </div>

      {isAdaptive && (
        <dl className="grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt className="text-zinc-500">Converged</dt>
            <dd className={convergence.converged ? 'text-emerald-300' : 'text-amber-200'}>
              {convergence.converged ? 'Yes' : 'No'}
            </dd>
          </div>
          <div>
            <dt className="text-zinc-500">Stopping reason</dt>
            <dd className="font-mono text-zinc-200">{convergence.stopping_reason || '—'}</dd>
          </div>
          <div>
            <dt className="text-zinc-500">Iterations</dt>
            <dd className="font-mono text-zinc-200">
              {convergence.iterations_run ?? iterations.length ?? '—'} /{' '}
              {convergence.max_iterations ?? '—'}
            </dd>
          </div>
          <div>
            <dt className="text-zinc-500">Final error vs target</dt>
            <dd className="font-mono text-zinc-200">
              {convergence.final_error_abs != null
                ? `${(convergence.final_error_abs * 100).toFixed(3)} pp`
                : '—'}
            </dd>
          </div>
          <div>
            <dt className="text-zinc-500">Final corrected error</dt>
            <dd className="font-mono text-zinc-200">
              {convergence.final_error_abs_corrected != null
                ? `${(convergence.final_error_abs_corrected * 100).toFixed(3)} pp`
                : '—'}
            </dd>
          </div>
        </dl>
      )}

      {iterations.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[32rem] text-left text-xs">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-500">
                <th className="py-1 pr-2">#</th>
                <th className="py-1 pr-2">Estimate</th>
                <th className="py-1 pr-2">± stderr</th>
                <th className="py-1 pr-2">Shots</th>
                <th className="py-1 pr-2">Bins</th>
                <th className="py-1 pr-2">Error</th>
                <th className="py-1 pr-2">Corrected err</th>
                <th className="py-1 pr-2">Bins seen</th>
                <th className="py-1 pr-2">Action</th>
                <th className="py-1">σ</th>
              </tr>
            </thead>
            <tbody>
              {iterations.map((step) => (
                <tr key={step.iteration} className="border-b border-zinc-900/80 text-zinc-300">
                  <td className="py-1 pr-2 font-mono">{step.iteration}</td>
                  <td className="py-1 pr-2 font-mono">{pct(step.estimate)}</td>
                  <td className="py-1 pr-2 font-mono">{pct(step.standard_error)}</td>
                  <td className="py-1 pr-2 font-mono">{step.shots}</td>
                  <td className="py-1 pr-2 font-mono">{step.bins ?? '—'}</td>
                  <td className="py-1 pr-2 font-mono">
                    {step.error_to_target != null
                      ? `${step.error_to_target >= 0 ? '+' : ''}${(step.error_to_target * 100).toFixed(3)} pp`
                      : '—'}
                  </td>
                  <td className="py-1 pr-2 font-mono">
                    {step.error_to_target_corrected != null
                      ? `${step.error_to_target_corrected >= 0 ? '+' : ''}${(step.error_to_target_corrected * 100).toFixed(3)} pp`
                      : '—'}
                  </td>
                  <td className="py-1 pr-2 font-mono">
                    {step.distinct_bins_observed ?? '—'}
                  </td>
                  <td className="py-1 pr-2 font-mono">
                    {step.policy_action?.reason || '—'}
                  </td>
                  <td className="py-1 font-mono">
                    {step.error_sigma != null ? step.error_sigma.toFixed(2) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {result.databank_recorded && (
        <div className="rounded-lg border border-emerald-500/20 bg-emerald-950/20 p-2 text-xs text-emerald-200">
          Saved to local hardware databank
          {result.databank_path && (
            <p className="mt-1 break-all font-mono text-[10px] text-emerald-300/80">
              {result.databank_path}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
