import { getParticleModel } from '../data/particleModels'

export default function EventDetailCard({ event }) {
  if (!event) {
    return (
      <div className="rounded-xl border border-dashed border-neon-magenta/25 bg-black/60 p-6 text-center text-sm text-zinc-500 backdrop-blur-sm">
        Select a row to see event detail and the 3D particle view.
      </div>
    )
  }

  const meta = getParticleModel(event.particle?.name)
  const pdg = meta.pdgMass
  const delta = pdg != null ? event.M - pdg : null

  return (
    <div className="rounded-xl border border-neon-magenta/20 bg-black/80 p-5 shadow-inner shadow-black/30 backdrop-blur-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-zinc-500">Run / Event</p>
          <p className="font-mono text-lg text-white">
            {event.run} <span className="text-zinc-600">/</span> {event.event}
          </p>
        </div>
        <span
          className="rounded-full px-3 py-1 text-sm font-semibold"
          style={{
            backgroundColor: `${event.particle?.color || '#64748b'}33`,
            color: event.particle?.color || '#fafafa',
          }}
        >
          {event.particle?.symbol || '?'}
        </span>
      </div>
      <dl className="mt-4 grid grid-cols-3 gap-3 text-sm">
        <div>
          <dt className="text-zinc-500">E1</dt>
          <dd className="font-medium text-zinc-100">{event.E1?.toFixed(2)} GeV</dd>
        </div>
        <div>
          <dt className="text-zinc-500">E2</dt>
          <dd className="font-medium text-zinc-100">{event.E2?.toFixed(2)} GeV</dd>
        </div>
        <div>
          <dt className="text-zinc-500">M</dt>
          <dd className="font-medium text-zinc-100">{event.M?.toFixed(3)} GeV</dd>
        </div>
      </dl>
      <div className="mt-4 border-t border-neon-magenta/15 pt-4 text-sm text-zinc-300">
        <p className="font-display font-semibold text-white">{meta.label}</p>
        <p className="mt-1 text-zinc-400">{event.particle?.decay || meta.decay}</p>
        {pdg != null && (
          <p className="mt-2 text-xs text-zinc-500">
            PDG mass {pdg.toFixed(4)} GeV
            {delta != null && (
              <span className="text-neon-green"> · Δ {delta >= 0 ? '+' : ''}{delta.toFixed(3)} GeV</span>
            )}
          </p>
        )}
        {event.z_scores && (
          <p className="mt-2 font-mono text-xs text-zinc-500">
            z: E1 {event.z_scores.E1?.toFixed(2)} · E2 {event.z_scores.E2?.toFixed(2)} · M{' '}
            {event.z_scores.M?.toFixed(2)}
          </p>
        )}
      </div>
    </div>
  )
}
