import axios from 'axios'

const api = axios.create({ baseURL: '' })

export async function uploadCsv(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/api/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getStats() {
  const { data } = await api.get('/api/stats')
  return data
}

export async function getSpectrum(bins = 200) {
  const { data } = await api.get('/api/spectrum', { params: { bins } })
  return data
}

export async function getOutliers({ limit = 100, offset = 0, known_only = false } = {}) {
  const { data } = await api.get('/api/outliers', {
    params: { limit, offset, known_only: known_only ? 'true' : 'false' },
  })
  return data
}

export async function getQuantumObservables() {
  const { data } = await api.get('/api/quantum/observables')
  return data
}

export async function getClassicalGroundTruth(particle = null) {
  const { data } = await api.get('/api/quantum/ground-truth', {
    params: particle ? { particle } : {},
  })
  return data
}

export async function submitQuantumJob({
  particle = null,
  mode = 'adaptive_snapshot',
  target_probability = null,
  mass_bins = 256,
  max_iterations = 20,
  epsilon = 0.00001,
  max_shots = 65536,
  max_bins = 256,
  allow_backend_switch = true,
  allow_symmetry_toggle = true,
} = {}) {
  const body = {
    mode,
    mass_bins,
    max_iterations,
    epsilon,
    max_shots,
    max_bins,
    allow_backend_switch,
    allow_symmetry_toggle,
  }
  if (particle) body.particle = particle
  if (target_probability != null) body.target_probability = target_probability
  const { data } = await api.post('/api/quantum/job', body)
  return data
}

export async function getQuantumDatabankSummary(top = 10) {
  const { data } = await api.get('/api/quantum/databank/summary', {
    params: { top },
  })
  return data
}

export async function getQuantumRuntimeStatus(probe = true) {
  const { data } = await api.get('/api/quantum/runtime', {
    params: probe ? { probe: 'true' } : {},
  })
  return data
}

export async function getQuantumResult(jobId) {
  const { data } = await api.get(`/api/quantum/result/${jobId}`)
  return data
}
