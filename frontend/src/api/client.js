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

export async function submitQuantumJob() {
  const { data } = await api.post('/api/quantum/job')
  return data
}

export async function getQuantumRuntimeStatus() {
  const { data } = await api.get('/api/quantum/runtime')
  return data
}

export async function getQuantumResult(jobId) {
  const { data } = await api.get(`/api/quantum/result/${jobId}`)
  return data
}
