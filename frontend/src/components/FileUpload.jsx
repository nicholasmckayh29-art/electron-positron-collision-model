import { useCallback, useState } from 'react'

export default function FileUpload({ onUploaded, disabled }) {
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const handle = useCallback(
    async (file) => {
      if (!file || !file.name.endsWith('.csv')) {
        setErr('Please drop a .csv file.')
        return
      }
      setErr(null)
      setBusy(true)
      try {
        await onUploaded(file)
      } catch (e) {
        setErr(e.response?.data?.detail || e.message || 'Upload failed')
      } finally {
        setBusy(false)
      }
    },
    [onUploaded],
  )

  return (
    <div
      className={`rounded-2xl border-2 border-dashed p-10 text-center transition-colors ${
        drag
          ? 'border-neon-green bg-neon-green/10'
          : 'border-neon-magenta/35 bg-black/75'
      } ${disabled ? 'pointer-events-none opacity-50' : ''}`}
      onDragOver={(e) => {
        e.preventDefault()
        setDrag(true)
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDrag(false)
        handle(e.dataTransfer.files[0])
      }}
    >
      <p className="font-display text-lg font-semibold text-white">Upload collision CSV</p>
      <p className="mt-2 text-sm text-zinc-400">
        CMS dielectron formats: wide (E1, E2, M), Zee-style (pt/eta/phi), or long per-electron rows
      </p>
      <label className="mt-6 inline-block cursor-pointer rounded-xl bg-neon-magenta px-5 py-2.5 text-sm font-semibold text-black hover:bg-neon-magenta/90">
        {busy ? 'Loading…' : 'Choose CSV'}
        <input
          type="file"
          accept=".csv"
          className="hidden"
          disabled={busy || disabled}
          onChange={(e) => handle(e.target.files?.[0])}
        />
      </label>
      {err && <p className="mt-4 text-sm text-rose-400">{String(err)}</p>}
    </div>
  )
}
