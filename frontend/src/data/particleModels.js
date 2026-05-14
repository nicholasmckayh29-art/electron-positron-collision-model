/** 3D scene metadata keyed by `particle.name` from the API. */
export const PARTICLE_MODELS = {
  eta: {
    label: 'η meson',
    pdgMass: 0.547862,
    decay: 'η → γγ',
    color: '#a8dadc',
  },
  rho_omega: {
    label: 'ρ / ω',
    pdgMass: 0.782,
    decay: 'ρ/ω → e⁺e⁻',
    color: '#457b9d',
  },
  phi: {
    label: 'φ meson',
    pdgMass: 1.019461,
    decay: 'φ → e⁺e⁻',
    color: '#1d3557',
  },
  jpsi: {
    label: 'J/ψ',
    pdgMass: 3.0969,
    decay: 'J/ψ → e⁺e⁻',
    color: '#e63946',
  },
  psi2s: {
    label: 'ψ(2S)',
    pdgMass: 3.6861,
    decay: 'ψ(2S) → e⁺e⁻',
    color: '#f4a261',
  },
  upsilon: {
    label: 'Υ family',
    pdgMass: 9.4603,
    decay: 'Υ → e⁺e⁻',
    color: '#2a9d8f',
  },
  z_boson: {
    label: 'Z⁰ boson',
    pdgMass: 91.1876,
    decay: 'Z⁰ → e⁺e⁻',
    color: '#e9c46a',
  },
  unknown: {
    label: 'Unknown / exotic candidate',
    pdgMass: null,
    decay: '—',
    color: '#94a3b8',
  },
}

export function getParticleModel(particleName) {
  return PARTICLE_MODELS[particleName] || PARTICLE_MODELS.unknown
}
