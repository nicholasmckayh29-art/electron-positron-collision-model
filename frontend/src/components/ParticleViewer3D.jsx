import { Suspense, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Html, Line, OrbitControls } from '@react-three/drei'
import { getParticleModel } from '../data/particleModels'

function Spin({ children }) {
  const ref = useRef(null)
  useFrame((_, dt) => {
    if (ref.current) ref.current.rotation.y += dt * 0.35
  })
  return <group ref={ref}>{children}</group>
}

function ZBosonScene({ color }) {
  return (
    <Spin>
      <mesh>
        <icosahedronGeometry args={[1.05, 1]} />
        <meshStandardMaterial color={color} metalness={0.25} roughness={0.4} />
      </mesh>
      <mesh position={[1.35, 0.25, 0]}>
        <sphereGeometry args={[0.14, 24, 24]} />
        <meshStandardMaterial color="#4ade80" emissive="#22c55e" emissiveIntensity={0.35} />
      </mesh>
      <mesh position={[-1.35, -0.25, 0]}>
        <sphereGeometry args={[0.14, 24, 24]} />
        <meshStandardMaterial color="#c084fc" emissive="#a855f7" emissiveIntensity={0.35} />
      </mesh>
    </Spin>
  )
}

function CharmoniumScene({ color }) {
  return (
    <Spin>
      <Line
        points={[
          [-0.45, 0, 0],
          [0.45, 0, 0],
        ]}
        color={color}
        lineWidth={2}
      />
      <mesh position={[-0.45, 0, 0]}>
        <sphereGeometry args={[0.35, 32, 32]} />
        <meshStandardMaterial color="#ef4444" />
      </mesh>
      <mesh position={[0.45, 0, 0]}>
        <sphereGeometry args={[0.35, 32, 32]} />
        <meshStandardMaterial color="#3b82f6" />
      </mesh>
    </Spin>
  )
}

function BottomoniumScene({ color }) {
  return (
    <Spin>
      <mesh position={[-0.55, 0, 0]}>
        <sphereGeometry args={[0.4, 32, 32]} />
        <meshStandardMaterial color="#22c55e" />
      </mesh>
      <mesh position={[0.55, 0, 0]}>
        <sphereGeometry args={[0.4, 32, 32]} />
        <meshStandardMaterial color="#15803d" />
      </mesh>
    </Spin>
  )
}

function LightMesonScene({ color }) {
  return (
    <Spin>
      <mesh>
        <octahedronGeometry args={[0.75, 0]} />
        <meshStandardMaterial color={color} metalness={0.15} roughness={0.45} />
      </mesh>
    </Spin>
  )
}

function ExoticScene() {
  const ref = useRef(null)
  useFrame((_, dt) => {
    if (ref.current) {
      ref.current.rotation.x += dt * 0.2
      ref.current.rotation.y += dt * 0.35
    }
  })
  return (
    <group ref={ref}>
      <mesh>
        <icosahedronGeometry args={[0.95, 0]} />
        <meshStandardMaterial color="#4ade80" wireframe emissive="#22c55e" emissiveIntensity={0.2} />
      </mesh>
    </group>
  )
}

function SceneSwitch({ name, color }) {
  switch (name) {
    case 'z_boson':
      return <ZBosonScene color={color} />
    case 'jpsi':
    case 'psi2s':
      return <CharmoniumScene color={color} />
    case 'upsilon':
      return <BottomoniumScene color={color} />
    case 'unknown':
      return <ExoticScene />
    default:
      return <LightMesonScene color={color} />
  }
}

export default function ParticleViewer3D({ particle, eventM }) {
  const name = particle?.name || 'unknown'
  const meta = getParticleModel(name)
  const color = particle?.color || meta.color

  return (
    <div className="h-[320px] w-full overflow-hidden rounded-xl border border-neon-green/25 bg-black">
      <Canvas camera={{ position: [0, 0.4, 3.2], fov: 45 }} gl={{ antialias: true }}>
        <color attach="background" args={['#000000']} />
        <ambientLight intensity={0.45} />
        <directionalLight position={[4, 6, 2]} intensity={1.1} />
        <Suspense fallback={null}>
          <SceneSwitch name={name} color={color} />
          <Html position={[0, -1.35, 0]} center>
            <div className="w-64 rounded-lg border border-neon-magenta/25 bg-charcoal/95 px-3 py-2 text-center text-xs text-zinc-200 shadow-lg backdrop-blur">
              <span className="font-semibold text-white">{meta.label}</span>
              {eventM != null && meta.pdgMass != null && (
                <p className="mt-1 text-zinc-400">
                  Event M: {eventM.toFixed(3)} GeV · PDG {meta.pdgMass.toFixed(3)} GeV
                </p>
              )}
            </div>
          </Html>
        </Suspense>
        <OrbitControls enablePan={false} minDistance={2} maxDistance={6} />
      </Canvas>
    </div>
  )
}
