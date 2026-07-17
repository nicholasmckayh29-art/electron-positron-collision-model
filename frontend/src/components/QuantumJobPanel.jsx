import { useCallback, useEffect, useRef, useState } from 'react'
import {
  getClassicalGroundTruth,
  getQuantumDatabankSummary,
  getQuantumObservables,
  getQuantumResult,
  getQuantumRuntimeStatus,
  submitQuantumJob,
} from '../api/client'
import AdaptiveConvergencePanel from './AdaptiveConvergencePanel.jsx'
import DatabankLeaderboard from './DatabankLeaderboard.jsx'
import GroundTruthValidation from './GroundTruthValidation.jsx'

export default function QuantumJobPanel({ ready, onComplete }) {
  const [observables, setObservables] = useState([])
  const [particle, setParticle] = useState('auto')
  const [mode, setMode] = useState('adaptive_snapshot')
  const [massBins, setMassBins] = useState(256)
  const [maxIterations, setMaxIterations] = useState(20)
  const [epsilon, setEpsilon] = useState(0.00001)
  const [maxShots, setMaxShots] = useState(65536)
  const [maxBins, setMaxBins] = useState(256)
  const [allowBackendSwitch, setAllowBackendSwitch] = useState(true)
  const [allowSymmetryToggle, setAllowSymmetryToggle] = useState(true)
  const [useCustomTarget, setUseCustomTarget] = useState(false)
  const [targetProbability, setTargetProbability] = useState('')
  const [classical, setClassical] = useState(null)
  const [classicalLoading, setClassicalLoading] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [runtime, setRuntime] = useState(null)
  const [databank, setDatabank] = useState(null)
  const [databankLoading, setDatabankLoading] = useState(false)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const timer = useRef(null)

  const clearTimer = () => {
    if (timer.current) {
      clearInterval(timer.current)
      timer.current = null
    }
  }

  const loadClassical = useCallback(async (selected) => {
    if (!ready) return
    setClassicalLoading(true)
    try {
      const gt = await getClassicalGroundTruth(selected === 'auto' ? null : selected)
      setClassical(gt)
      setErr(null)
    } catch (e) {
      setClassical(null)
      setErr(e.response?.data?.detail || e.message)
    } finally {
      setClassicalLoading(false)
    }
  }, [ready])

  const loadDatabank = useCallback(async () => {
    setDatabankLoading(true)
    try {
      const summary = await getQuantumDatabankSummary(10)
      setDatabank(summary)
    } catch (e) {
      setDatabank(null)
    } finally {
      setDatabankLoading(false)
    }
  }, [])

  useEffect(() => {
    getQuantumObservables()
      .then((r) => setObservables(r.observables || []))
      .catch(() => setObservables([]))
    getQuantumRuntimeStatus()
      .then(setRuntime)
      .catch(() => setRuntime(null))
    loadDatabank()
  }, [loadDatabank])

  useEffect(() => {
    if (ready) loadClassical(particle)
  }, [ready, particle, loadClassical])

  const poll = useCallback(
    async (id) => {
      try {
        const r = await getQuantumResult(id)
        setStatus(r)
        if (r.status === 'completed') {
          clearTimer()
          setBusy(false)
          onComplete?.()
          loadDatabank()
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
    [loadDatabank, onComplete],
  )

  useEffect(() => () => clearTimer(), [])

  const start = async () => {
    clearTimer()
    setErr(null)
    setBusy(true)
    setStatus(null)

    let target = null
    if (useCustomTarget && targetProbability !== '') {
      target = Number(targetProbability)
      if (Number.isNaN(target) || target < 0 || target > 1) {
        setErr('Target probability must be a number between 0 and 1')
        setBusy(false)
        return
      }
    }

    try {
      const jobParams = {
        particle: particle === 'auto' ? null : particle,
        mode,
        target_probability: target,
        mass_bins: Number(massBins),
        max_iterations: Number(maxIterations),
        epsilon: Number(epsilon),
        max_shots: Number(maxShots),
        max_bins: Number(maxBins),
        allow_backend_switch: allowBackendSwitch,
        allow_symmetry_toggle: allowSymmetryToggle,
      }
      const r = await submitQuantumJob(jobParams)
      setJobId(r.job_id)
      setStatus({ status: r.status, total: r.total, processed: 0, message: r.message })
      clearTimer()
      timer.current = setInterval(() => poll(r.job_id), 2000)
      poll(r.job_id)
    } catch (e) {
      setErr(e.response?.data?.detail || e.message)
      setBusy(false)
    }
  }

  const disabled = !ready || busy
  const exactTarget = classical?.exact_classical_probability

  return (
    <section className="space-y-4">
      <div className="rounded-xl border border-neon-magenta/20 bg-black/80 p-4 shadow-inner shadow-black/30 backdrop-blur-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-lg font-semibold text-white">
              Quantum verification
            </h2>
            <p className="text-xs text-zinc-500">
              Compare resonance window probability: exact → binned → quantum sample.{' '}
              {runtime?.real_backend_enabled ? 'IBM Runtime' : 'Local simulator'}.
            </p>
          </div>
          <button
            type="button"
            disabled={disabled}
            onClick={start}
            className="rounded-xl bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-500 disabled:opacity-50"
          >
            {busy ? 'Running…' : mode === 'adaptive_snapshot' ? 'Run adaptive job' : 'Run snapshot job'}
          </button>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <label className="flex flex-col gap-1 text-xs text-zinc-500">
            Resonance window
            <select
              value={particle}
              disabled={!ready || busy}
              onChange={(e) => setParticle(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-200"
            >
              {observables.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-zinc-500">
            Mode
            <select
              value={mode}
              disabled={!ready || busy}
              onChange={(e) => setMode(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-200"
            >
              <option value="adaptive_snapshot">Adaptive (thermostat loop)</option>
              <option value="snapshot">Snapshot (single run)</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-zinc-500">
            Max iterations
            <input
              type="number"
              min={1}
              max={50}
              value={maxIterations}
              disabled={!ready || busy || mode !== 'adaptive_snapshot'}
              onChange={(e) => setMaxIterations(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-200 disabled:opacity-40"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs text-zinc-500">
            Epsilon (target tolerance, probability units)
            <input
              type="number"
              min={0.0000001}
              step={0.000001}
              value={epsilon}
              disabled={!ready || busy || mode !== 'adaptive_snapshot'}
              onChange={(e) => setEpsilon(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-200 disabled:opacity-40"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-zinc-500">
            Mass bins (2^n padded)
            <input
              type="number"
              min={2}
              step={2}
              value={massBins}
              disabled={!ready || busy}
              onChange={(e) => setMassBins(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-200"
            />
          </label>
        </div>

        {mode === 'adaptive_snapshot' && (
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <label className="flex flex-col gap-1 text-xs text-zinc-500">
              Max shots budget
              <input
                type="number"
                min={128}
                step={128}
                value={maxShots}
                disabled={!ready || busy}
                onChange={(e) => setMaxShots(e.target.value)}
                className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-200"
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-zinc-500">
              Max mass bins
              <input
                type="number"
                min={2}
                step={2}
                value={maxBins}
                disabled={!ready || busy}
                onChange={(e) => setMaxBins(e.target.value)}
                className="rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-200"
              />
            </label>
            <label className="flex items-center gap-2 text-xs text-zinc-400">
              <input
                type="checkbox"
                checked={allowBackendSwitch}
                disabled={!ready || busy}
                onChange={(e) => setAllowBackendSwitch(e.target.checked)}
              />
              Allow backend switching
            </label>
            <label className="flex items-center gap-2 text-xs text-zinc-400">
              <input
                type="checkbox"
                checked={allowSymmetryToggle}
                disabled={!ready || busy}
                onChange={(e) => setAllowSymmetryToggle(e.target.checked)}
              />
              Allow symmetry toggle
            </label>
          </div>
        )}

        {mode === 'adaptive_snapshot' && (
          <div className="mt-3 flex flex-wrap items-end gap-3">
            <label className="flex items-center gap-2 text-xs text-zinc-400">
              <input
                type="checkbox"
                checked={useCustomTarget}
                disabled={!ready || busy}
                onChange={(e) => setUseCustomTarget(e.target.checked)}
              />
              Custom target probability
            </label>
            {useCustomTarget ? (
              <label className="flex flex-col gap-1 text-xs text-zinc-500">
                Target P(window)
                <input
                  type="number"
                  min={0}
                  max={1}
                  step={0.0001}
                  value={targetProbability}
                  disabled={!ready || busy}
                  onChange={(e) => setTargetProbability(e.target.value)}
                  className="w-40 rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-200"
                />
              </label>
            ) : (
              <p className="text-xs text-zinc-500">
                Target defaults to exact classical probability
                {exactTarget != null ? `: ${(exactTarget * 100).toFixed(3)}%` : ''}
                {' · '}
                stop when error ≤ {(Number(epsilon) * 100).toFixed(4)} pp
              </p>
            )}
          </div>
        )}

        {classicalLoading && (
          <p className="mt-2 text-xs text-zinc-500">Updating classical baseline…</p>
        )}

        {!ready && (
          <p className="mt-2 text-xs text-zinc-500">Upload a CSV to preview ground truth and run jobs.</p>
        )}

        {ready && classical && (
          <GroundTruthValidation classical={classical} quantum={status?.result} />
        )}

        {status?.result && (
          <AdaptiveConvergencePanel result={status.result} />
        )}

        {jobId && (
          <p className="mt-3 font-mono text-xs text-zinc-500">
            job_id: <span className="text-zinc-300">{jobId}</span>
          </p>
        )}
        {status && status.status !== 'completed' && (
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
          <div className="mt-2 space-y-1 text-xs text-zinc-500">
            <p>
              Runtime:{' '}
              <span className={runtime.real_backend_enabled ? 'text-cyan-300' : 'text-zinc-300'}>
                {runtime.real_backend_enabled ? 'IBM enabled' : 'local simulator'}
              </span>
              {runtime.requested_backend ? ` · ${runtime.requested_backend}` : ''}
              {runtime.real_backend_enabled && !runtime.token_configured ? ' · token missing' : ''}
              {runtime.ibm_ready === true && ' · IBM probe OK'}
              {runtime.ibm_ready === false && ' · IBM probe failed'}
            </p>
            {runtime.databank_enabled && (
              <p className="text-zinc-400">
                Databank: {runtime.databank_path || 'data/quantum_databank/hardware_runs.jsonl'}
              </p>
            )}
            {runtime.instance_hint && (
              <p className="text-amber-200/90">{runtime.instance_hint}</p>
            )}
            {runtime.ibm_probe && !runtime.ibm_probe.ok && (
              <p className="text-rose-300">
                {runtime.ibm_probe.error}
                {runtime.ibm_probe.hint ? ` — ${runtime.ibm_probe.hint}` : ''}
              </p>
            )}
            {runtime.ibm_probe?.ok && runtime.ibm_probe.hardware_backends_sample?.length > 0 && (
              <p className="text-zinc-400">
                Instance {runtime.ibm_probe.instance ?? 'auto'} · hardware:{' '}
                {runtime.ibm_probe.hardware_backends_sample.slice(0, 4).join(', ')}
              </p>
            )}
          </div>
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
                <p className="font-mono break-all">{status.result.runtime_job_id}</p>
              </div>
            )}
            <div>
              <span className="text-zinc-500">Pipeline mode</span>
              <p className="font-mono">{status.result.pipeline_mode}</p>
            </div>
            <div>
              <span className="text-zinc-500">Shots</span>
              <p>{status.result.shots}</p>
            </div>
            <div>
              <span className="text-zinc-500">Bias-corrected estimate</span>
              <p>
                {status.result.convergence?.final_estimate_corrected != null
                  ? `${(status.result.convergence.final_estimate_corrected * 100).toFixed(3)}%`
                  : '—'}
              </p>
            </div>
            <div>
              <span className="text-zinc-500">Stop policy reason</span>
              <p className="font-mono">{status.result.convergence?.stopping_reason || '—'}</p>
            </div>
            <div>
              <span className="text-zinc-500">Circuit</span>
              <p>
                {status.result.circuit?.qubits} qubits · depth {status.result.circuit?.depth}
              </p>
            </div>
            <div>
              <span className="text-zinc-500">Bins observed</span>
              <p>
                {status.result.circuit?.distinct_bins_observed ?? '—'} / {status.result.circuit?.bins ?? '—'}
              </p>
            </div>
          </div>
        )}

        {err && <p className="mt-2 text-sm text-rose-400">{err}</p>}
      </div>

      <DatabankLeaderboard
        summary={databank}
        loading={databankLoading}
        onRefresh={loadDatabank}
      />
    </section>
  )
}
