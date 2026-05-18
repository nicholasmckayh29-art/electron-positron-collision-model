import { useCallback, useMemo, useState } from 'react'
import CosmicBackground from './components/CosmicBackground.jsx'
import FileUpload from './components/FileUpload.jsx'
import StatsPanel from './components/StatsPanel.jsx'
import MassSpectrum from './components/MassSpectrum.jsx'
import OutlierTable from './components/OutlierTable.jsx'
import EventDetailCard from './components/EventDetailCard.jsx'
import ParticleViewer3D from './components/ParticleViewer3D.jsx'
import QuantumJobPanel from './components/QuantumJobPanel.jsx'
import { getOutliers, getSpectrum, getStats, uploadCsv } from './api/client.js'

const PAGE = 100
const OVERLAY = 500

export default function App() {
  const [ready, setReady] = useState(false)
  const [stats, setStats] = useState(null)
  const [spectrum, setSpectrum] = useState(null)
  const [outliersPage, setOutliersPage] = useState(null)
  const [overlayOutliers, setOverlayOutliers] = useState([])
  const [offset, setOffset] = useState(0)
  const [knownOnly, setKnownOnly] = useState(false)
  const [selected, setSelected] = useState(null)
  const [massRange, setMassRange] = useState(null)

  const loadOutliers = useCallback(async (off = offset, known = knownOnly) => {
    const data = await getOutliers({ limit: PAGE, offset: off, known_only: known })
    setOutliersPage(data)
  }, [offset, knownOnly])

  const loadOverlay = useCallback(async (known = knownOnly) => {
    const data = await getOutliers({ limit: OVERLAY, offset: 0, known_only: known })
    setOverlayOutliers(data.outliers || [])
  }, [knownOnly])

  const onUploaded = useCallback(async (file) => {
    await uploadCsv(file)
    const [st, sp] = await Promise.all([getStats(), getSpectrum(200)])
    setStats(st)
    setSpectrum(sp)
    setReady(true)
    setOffset(0)
    setSelected(null)
    const first = await getOutliers({ limit: PAGE, offset: 0, known_only: knownOnly })
    setOutliersPage(first)
    const ov = await getOutliers({ limit: OVERLAY, offset: 0, known_only: knownOnly })
    setOverlayOutliers(ov.outliers || [])
    const mmin = Math.min(...sp.edges)
    const mmax = Math.max(...sp.edges)
    setMassRange([mmin, mmax])
  }, [knownOnly])

  const spectrumDomain = useMemo(() => {
    if (massRange) return massRange
    if (!spectrum?.edges?.length) return [0, 120]
    return [spectrum.edges[0], spectrum.edges[spectrum.edges.length - 1]]
  }, [massRange, spectrum])

  const onBarClick = useCallback((row) => {
    if (!row || row.lo == null) return
    setMassRange([row.lo, row.hi])
  }, [])

  const onKnownOnlyChange = async (v) => {
    setKnownOnly(v)
    setOffset(0)
    const data = await getOutliers({ limit: PAGE, offset: 0, known_only: v })
    setOutliersPage(data)
    const ov = await getOutliers({ limit: OVERLAY, offset: 0, known_only: v })
    setOverlayOutliers(ov.outliers || [])
  }

  const onPage = async (newOffset) => {
    setOffset(newOffset)
    const data = await getOutliers({ limit: PAGE, offset: newOffset, known_only: knownOnly })
    setOutliersPage(data)
  }

  return (
    <>
      <CosmicBackground />
      <div className="relative z-10 min-h-screen bg-transparent pb-16 text-zinc-50">
        <header className="border-b border-neon-magenta/25 bg-charcoal/90 backdrop-blur-md">
          <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-8 sm:px-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-neon-magenta [text-shadow:0_0_24px_rgba(192,132,252,0.45)]">
              CMS dielectrons
            </p>
            <h1 className="font-display text-3xl font-bold text-white sm:text-4xl">
              Quantum particle collision visualizer
            </h1>
            <p className="max-w-2xl text-sm text-zinc-400">
              Upload collision CSV, explore the invariant-mass spectrum with PDG reference lines, inspect
              statistical outliers, view a schematic 3D particle, then run a QMC-style mass-window
              probability estimate.
            </p>
          </div>
        </header>

        <main className="mx-auto max-w-6xl space-y-10 px-4 py-10 sm:px-6">
          <FileUpload onUploaded={onUploaded} disabled={false} />

          {ready && (
            <>
              <section className="space-y-4">
                <h2 className="font-display text-lg font-semibold text-white">Dataset statistics</h2>
                <StatsPanel stats={stats} />
              </section>

              <section className="space-y-4">
                <div className="flex flex-wrap items-end justify-between gap-3">
                  <h2 className="font-display text-lg font-semibold text-white">Invariant mass spectrum</h2>
                  <button
                    type="button"
                    className="text-xs text-neon-green hover:text-neon-green/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-magenta/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black"
                    onClick={() => {
                      if (!spectrum?.edges?.length) return
                      setMassRange([spectrum.edges[0], spectrum.edges[spectrum.edges.length - 1]])
                    }}
                  >
                    Reset mass zoom
                  </button>
                </div>
                <MassSpectrum
                  spectrum={spectrum}
                  outliers={overlayOutliers}
                  massRange={spectrumDomain}
                  onBarClick={onBarClick}
                />
                <p className="text-xs text-zinc-500">
                  Bins containing outliers tint red (up to {OVERLAY} loaded rows for overlay). Click a bin to
                  zoom the axis to that mass window.
                </p>
              </section>

              <QuantumJobPanel
                onComplete={() => {
                  loadOutliers(offset, knownOnly)
                  loadOverlay(knownOnly)
                }}
              />

              <section className="space-y-4">
                <h2 className="font-display text-lg font-semibold text-white">Outliers</h2>
                <OutlierTable
                  page={outliersPage}
                  total={outliersPage?.total ?? 0}
                  limit={PAGE}
                  offset={offset}
                  onPage={onPage}
                  onSelect={setSelected}
                  selected={selected}
                  knownOnly={knownOnly}
                  onKnownOnlyChange={onKnownOnlyChange}
                />
              </section>

              <section className="grid gap-6 lg:grid-cols-2">
                <EventDetailCard event={selected} />
                <ParticleViewer3D particle={selected?.particle} eventM={selected?.M} />
              </section>
            </>
          )}
        </main>
      </div>
    </>
  )
}
