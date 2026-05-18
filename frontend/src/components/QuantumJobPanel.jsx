import { useCallback, useEffect, useRef, useState } from 'react'
import { getQuantumResult, getQuantumRuntimeStatus, submitQuantumJob } from '../api/client'

export default function QuantumJobPanel({ onComplete }) {
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [runtime, setRuntime] = useState(null)
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

  useEffect(() => {
    getQuantumRuntimeStatus()
      .then(setRuntime)
      .catch(() => setRuntime(null))
  }, [])

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
            QMC mass-window observable ·{' '}
            {runtime?.real_backend_enabled ? 'IBM Runtime hardware mode' : 'local simulator mode'}.
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
          {status.message && <p className="mt-1 text-xs text-zinc-500">{status.message}</p>}
        </div>
      )}
      {runtime && (
        <p className="mt-2 text-xs text-zinc-500">
          Runtime:{' '}
          <span className={runtime.real_backend_enabled ? 'text-cyan-300' : 'text-zinc-300'}>
            {runtime.real_backend_enabled ? 'IBM enabled' : 'local'}
          </span>
          {runtime.requested_backend ? ` · backend ${runtime.requested_backend}` : ''}
          {runtime.real_backend_enabled && !runtime.token_configured ? ' · token missing' : ''}
        </p>
      )}
      {status?.result && (
        <div className="mt-3 grid gap-2 rounded-lg border border-amber-400/10 bg-zinc-950/80 p-3 text-xs text-zinc-300 sm:grid-cols-2">
          <div>
            <span className="text-zinc-500">Observable</span>
            <p className="font-medium text-amber-100">{status.result.observable?.label}</p>
          </div>
          <div>
            <span className="text-zinc-500">Backend</span>
            <p className="font-mono">{status.result.backend}</p>
          </div>
          {status.result.runtime_job_id && (
            <div>
              <span className="text-zinc-500">IBM job</span>
              <p className="font-mono">{status.result.runtime_job_id}</p>
            </div>
          )}
          <div>
            <span className="text-zinc-500">Quantum estimate</span>
            <p>
              {status.result.estimate?.toFixed(4)} ±{' '}
              {status.result.standard_error?.toFixed(4)}
            </p>
          </div>
          <div>
            <span className="text-zinc-500">Classical baseline</span>
            <p>{status.result.exact_classical_probability?.toFixed(4)}</p>
          </div>
          <div>
            <span className="text-zinc-500">Shots</span>
            <p>{status.result.shots}</p>
          </div>
          <div>
            <span className="text-zinc-500">Circuit</span>
            <p>
              {status.result.circuit?.qubits} qubits · depth {status.result.circuit?.depth}
            </p>
          </div>
        </div>
      )}
      {err && <p className="mt-2 text-sm text-rose-400">{err}</p>}
    </div>
  )
}
