# Particle Identification — Scientific Background

This document is the research basis for the mass windows hard-coded in
[`backend/services/analysis.py`](../../backend/services/analysis.py)
(`PARTICLE_WINDOWS` and `identify_particle()`).

All cited papers and dataset records are mirrored locally under
[`papers/`](papers/) and [`opendata/`](opendata/) so the repo is
self-contained offline.

---

## Primary references (local copies)

| # | Reference | Local file | Used for |
|---|-----------|------------|----------|
| 1 | CMS Collaboration, *Performance of Electron Reconstruction and Selection with the CMS Detector in Proton-Proton Collisions at √s = 8 TeV*, JINST 10 P06005 (2015), **arXiv:1502.02701** | [`papers/CMS-electron-reconstruction-8TeV-arXiv-1502.02701.pdf`](papers/CMS-electron-reconstruction-8TeV-arXiv-1502.02701.pdf) | Electron momentum resolution (1.7–4.5%); justification for J/ψ and ψ(2S) window widths |
| 2 | CMS Collaboration, *Measurement of the differential Drell-Yan cross section in pp collisions at √s = 13 TeV*, **arXiv:1909.04133** | [`papers/CMS-Z-cross-section-arXiv-1909.04133.pdf`](papers/CMS-Z-cross-section-arXiv-1909.04133.pdf) | Standard \|m − 91.1876\| < 15 GeV Z⁰ fiducial window |
| 3 | CERN Open Data **record 302** — Dielectron events 2010, J/ψ candidates | [`opendata/record-302-Jpsi-ElEl-2010.html`](opendata/record-302-Jpsi-ElEl-2010.html) | Source dataset (`Jpsi_ElEl_2010.csv`); selection range 2–5 GeV |
| 4 | CERN Open Data **record 305** — Dielectron events 2010, Υ candidates | [`opendata/record-305-Upsilon-ElEl-2010.html`](opendata/record-305-Upsilon-ElEl-2010.html) | Source dataset (`Upsilon_ElEl_2010.csv`); selection range 8–12 GeV |

Upstream URLs for the same files (in case you want the live versions):

- `https://arxiv.org/abs/1502.02701`
- `https://arxiv.org/abs/1909.04133`
- `https://opendata.cern.ch/record/302`
- `https://opendata.cern.ch/record/305`

---

## Mass windows (current `PARTICLE_WINDOWS`)

| Particle | Symbol | PDG mass (GeV) | ±Window (GeV) | Window range | Quark content | Primary source |
|----------|--------|---------------:|--------------:|--------------|---------------|----------------|
| eta | η | 0.548 | 0.06 | 0.488 – 0.608 | uū+dd̄+ss̄ | PDG (below data floor for `dielectron.csv`; kept for future low-mass datasets) |
| rho/omega | ρ/ω | 0.778 | 0.06 | 0.718 – 0.838 | uū+dd̄ | PDG (below data floor) |
| phi | φ | 1.019 | 0.03 | 0.989 – 1.049 | ss̄ | PDG (below data floor) |
| J/ψ | J/ψ | 3.097 | 0.15 | 2.947 – 3.247 | cc̄ | CERN OD #302 (2–5 GeV selection); resolution from arXiv:1502.02701 |
| ψ(2S) | ψ(2S) | 3.686 | 0.15 | 3.536 – 3.836 | cc̄ | Same resolution regime as J/ψ (arXiv:1502.02701) |
| Υ family | Υ | 9.460 | 1.50 | 7.960 – 10.960 | bb̄ | CERN OD #305 (8–12 GeV selection); CMS dielectron resolution cannot resolve Υ(1S/2S/3S) separately |
| Z boson | Z⁰ | 91.1876 | 15.0 | 76.190 – 106.190 | — | arXiv:1909.04133 (standard CMS fiducial window) |

> The η, ρ/ω, φ windows are defined in code but never fire for the bundled
> `dielectron.csv`, whose minimum invariant mass is **M ≈ 2.04 GeV**. They
> remain in `PARTICLE_WINDOWS` so the same code generalizes to lower-mass
> datasets (e.g. future J/ψ-only or φ-only open data files).

---

## Why these widths?

The CMS detector measures dielectron invariant mass with finite resolution
driven by bremsstrahlung energy loss in the silicon tracker before the
electron reaches the ECAL. From **arXiv:1502.02701** (CMS electron
reconstruction performance):

- Barrel (`|η| < 1.479`): momentum resolution **≈ 1.7%**
- Endcap (`|η| > 1.479`): momentum resolution **up to 4.5%**

At the Z⁰ peak (M ≈ 91 GeV) a 4.5% resolution alone implies ±4.1 GeV
*per electron*, and the dielectron invariant mass smearing roughly adds in
quadrature. The CMS Z cross-section analysis (**arXiv:1909.04133**) uses
\|m − M_Z\| < 15 GeV as its standard fiducial window — that is the source
of our `±15 GeV` Z⁰ window.

For the Υ family, CMS explicitly states in their dielectron analyses that
the three Υ states (1S, 2S, 3S) cannot be resolved separately in the e⁺e⁻
channel with this resolution; we therefore treat them as a single
**"Υ family"** window centered on 9.460 GeV with ±1.5 GeV, encompassing
all three (9.46 / 10.02 / 10.36 GeV).

For J/ψ and ψ(2S), CERN Open Data record 302 selects dielectron events in
the broad 2–5 GeV window; we use a tighter ±0.15 GeV around each
nominal mass for cleaner peak identification.

---

## How this maps to the code

The constants below live in
[`backend/services/analysis.py`](../../backend/services/analysis.py).

```python
PARTICLE_WINDOWS = [
    {"name": "eta",       "mass": 0.548,   "width": 0.06},
    {"name": "rho_omega", "mass": 0.778,   "width": 0.06},
    {"name": "phi",       "mass": 1.019,   "width": 0.03},
    {"name": "jpsi",      "mass": 3.097,   "width": 0.15},
    {"name": "psi2s",     "mass": 3.686,   "width": 0.15},
    {"name": "upsilon",   "mass": 9.460,   "width": 1.50},
    {"name": "z_boson",   "mass": 91.1876, "width": 15.0},
]

def identify_particle(mass_gev: float) -> dict:
    for p in PARTICLE_WINDOWS:
        if abs(mass_gev - p["mass"]) <= p["width"]:
            return p
    return {"name": "unknown", ...}
```

**If you change any width**, update both this document and the
corresponding "Decision Log" row in
[`docs/backend-toolkit.md`](../backend-toolkit.md).

---

## Future refinements

Suggested upgrades (none implemented yet):

1. **Breit–Wigner weighting** instead of a rectangular window — give each
   match a confidence score using the particle's natural width Γ from PDG.
2. **Resolution-aware widths** that scale with electron \|η\| (barrel vs
   endcap), reflecting the 1.7% vs 4.5% momentum-resolution split from
   arXiv:1502.02701.
3. **Tighter Z⁰ window** (e.g. ±5 GeV) when only the resonance core is of
   interest; ±15 GeV is the standard CMS fiducial cut but includes
   significant Drell–Yan continuum.
4. **Separate Υ(1S), Υ(2S), Υ(3S)** for datasets with higher resolution
   (dimuon channel, future open data) — currently merged because the
   dielectron channel cannot resolve them.
