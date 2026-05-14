import { useCallback, useEffect, useRef, useState } from 'react'
import { getQuantumResult, submitQuantumJob } from '../api/client'

export default function QuantumJobPanel({ onComplete }) {
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const timer = useRef(null)

  const clearTimer = () => {
    if (timer.current) {
      clearInterval(timer.current)
      timer.current = null
    }
  }

  const poll = useCallback(
    async (id) => {
      try {
        const r = await getQuantumResult(id)
        setStatus(r)
        if (r.status === 'completed') {
          clearTimer()
          setBusy(false)
          onComplete?.()
        } else if (r.status === 'failed') {
          clearTimer()
          setBusy(false)
          setErr(r.error || 'Quantum job failed')
        }
      } catch (e) {
        setErr(e.response?.data?.detail || e.message)
        clearTimer()
        setBusy(false)
      }
    },
    [onComplete],
  )

  useEffect(() => () => clearTimer(), [])

  const start = async () => {
    clearTimer()
    setErr(null)
    setBusy(true)
    setStatus(null)
    try {
      const r = await submitQuantumJob()
      setJobId(r.job_id)
      setStatus({ status: r.status, total: r.total, processed: 0 })
      clearTimer()
      timer.current = setInterval(() => poll(r.job_id), 2000)
      poll(r.job_id)
    } catch (e) {
      setErr(e.response?.data?.detail || e.message)
      setBusy(false)
    }
  }

  return (
    <div className="rounded-xl border border-neon-magenta/20 bg-black/80 p-4 shadow-inner shadow-black/30 backdrop-blur-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-display text-sm font-semibold text-white">Quantum analysis</h3>
          <p className="text-xs text-zinc-500">
            Aer Estimator · ⟨ZZZ⟩ per outlier (batched). Re-fetch table when complete.
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={start}
          className="rounded-xl bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-500 disabled:opacity-50"
        >
          {busy ? 'Running…' : 'Run quantum job'}
        </button>
      </div>
      {jobId && (
        <p className="mt-3 font-mono text-xs text-zinc-500">
          job_id: <span className="text-zinc-300">{jobId}</span>
        </p>
      )}
      {status && (
        <div className="mt-2 text-sm text-zinc-300">
          <span className="font-medium capitalize text-amber-200">{status.status}</span>
          {status.total > 0 && (
            <span className="ml-2 text-zinc-500">
              {status.processed ?? 0} / {status.total}
            </span>
          )}
        </div>
      )}
      {err && <p className="mt-2 text-sm text-rose-400">{err}</p>}
    </div>
  )
}
