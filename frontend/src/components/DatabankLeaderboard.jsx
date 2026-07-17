/** Pathway efficiency leaderboard from saved hardware runs. */

export default function DatabankLeaderboard({ summary, loading, onRefresh }) {
  const count = summary?.record_count ?? 0
  const leaderboard = summary?.leaderboard ?? []
  const recent = summary?.recent_runs ?? []

  return (
    <div className="mt-3 space-y-3 rounded-lg border border-cyan-500/20 bg-zinc-950/90 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-cyan-200/90">
            Hardware databank
          </h4>
          <p className="text-[11px] text-zinc-500">
            {count} saved run{count === 1 ? '' : 's'}
            {summary?.databank_path ? ` · ${summary.databank_path}` : ''}
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="rounded-lg border border-zinc-700 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
        >
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {count === 0 ? (
        <p className="text-xs text-zinc-500">
          No hardware runs saved yet. Complete an IBM Runtime job to populate the databank.
        </p>
      ) : (
        <>
          <div>
            <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-zinc-500">
              Top pathways (lower score is better)
            </p>
            <div className="space-y-2">
              {leaderboard.map((row, i) => (
                <div
                  key={row.pathway}
                  className="rounded-lg border border-zinc-800 bg-black/40 p-2 text-xs"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono text-cyan-200">#{i + 1}</span>
                    <span className="text-zinc-500">{row.runs} run{row.runs === 1 ? '' : 's'}</span>
                  </div>
                  <p className="mt-1 break-all font-mono text-[10px] text-zinc-400">{row.pathway}</p>
                  <dl className="mt-2 grid grid-cols-2 gap-1 text-[11px] sm:grid-cols-4">
                    <div>
                      <dt className="text-zinc-600">Score</dt>
                      <dd className="font-mono text-zinc-200">
                        {row.avg_efficiency_score?.toFixed(5)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-zinc-600">Abs err</dt>
                      <dd className="font-mono text-zinc-200">
                        {(row.avg_abs_error_vs_exact * 100).toFixed(3)} pp
                      </dd>
                    </div>
                    <div>
                      <dt className="text-zinc-600">Shots</dt>
                      <dd className="font-mono text-zinc-200">{row.avg_shots?.toFixed(0)}</dd>
                    </div>
                    <div>
                      <dt className="text-zinc-600">Converged</dt>
                      <dd className="font-mono text-zinc-200">
                        {(row.converged_rate * 100).toFixed(0)}%
                      </dd>
                    </div>
                  </dl>
                </div>
              ))}
            </div>
          </div>

          {recent.length > 0 && (
            <div>
              <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-zinc-500">
                Recent runs
              </p>
              <div className="space-y-1">
                {recent.slice(0, 5).map((run) => (
                  <div
                    key={`${run.saved_at_utc}-${run.runtime_job_id}`}
                    className="flex flex-wrap items-center justify-between gap-2 rounded border border-zinc-900 px-2 py-1 text-[11px] text-zinc-400"
                  >
                    <span>
                      {run.particle} · {run.mode} · {run.backend}
                    </span>
                    <span className="font-mono text-zinc-500">{run.saved_at_utc}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
