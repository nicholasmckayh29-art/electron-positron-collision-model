import { useEffect, useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

const frag = /* glsl */ `
uniform vec3 uColor;
varying float vBright;
void main() {
  gl_FragColor = vec4(uColor * vBright, 1.0);
}
`

const ceilingVert = /* glsl */ `
uniform float uTime;
varying float vBright;
void main() {
  vec3 transformed = position;
  float t = uTime;
  float ax = transformed.x;
  float ay = transformed.y;
  transformed.z += 0.045 * sin(ax * 0.32 + t * 0.18) * sin(ay * 0.28 - t * 0.14);
  vBright = 0.9 + 0.08 * sin(t * 0.45);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(transformed, 1.0);
}
`

const floorVert = /* glsl */ `
uniform float uTime;
varying float vBright;
void main() {
  vec3 transformed = position;
  float t = uTime;
  float ax = transformed.x;
  float ay = transformed.y;
  float ripple = 0.12 * sin(ax * 0.46 + t * 0.28) * cos(ay * 0.5 + t * 0.19);
  vec2 c1 = vec2(sin(t * 0.11) * 5.0, cos(t * 0.095) * 4.0);
  vec2 c2 = vec2(cos(t * 0.075) * 3.6, sin(t * 0.13) * 4.4);
  float d1 = distance(vec2(ax, ay), c1);
  float d2 = distance(vec2(ax, ay), c2);
  float w1 = exp(-0.1 * d1 * d1) * 0.48;
  float w2 = exp(-0.12 * d2 * d2) * 0.34;
  float pulse = 1.0 + 0.032 * sin(t * 0.62);
  transformed.z += (ripple + (w1 + w2) * pulse) * 0.92;
  vBright = 0.86 + 0.14 * pulse;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(transformed, 1.0);
}
`

function ShaderGrid({ vertexShader, color, rotation, position, segments = 36 }) {
  const mat = useRef(null)
  const clock = useRef(0)

  useFrame((_, delta) => {
    if (typeof document !== 'undefined' && document.visibilityState !== 'visible') return
    if (!mat.current) return
    clock.current += delta
    mat.current.uniforms.uTime.value = clock.current
  })

  const uniforms = useRef({
    uTime: { value: 0 },
    uColor: { value: new THREE.Color(color) },
  })

  return (
    <mesh rotation={rotation} position={position}>
      <planeGeometry args={[26, 26, segments, segments]} />
      <shaderMaterial
        ref={mat}
        uniforms={uniforms.current}
        vertexShader={vertexShader}
        fragmentShader={frag}
        wireframe
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}

function Scene() {
  return (
    <>
      <ShaderGrid
        vertexShader={ceilingVert}
        color="#b855f7"
        rotation={[Math.PI / 2, 0, 0]}
        position={[0, 5.2, -1.2]}
      />
      <ShaderGrid
        vertexShader={floorVert}
        color="#4ade80"
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -5.2, -1.2]}
      />
    </>
  )
}

function usePrefersReducedMotion() {
  const [reduce, setReduce] = useState(false)
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return undefined
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const apply = () => setReduce(mq.matches)
    apply()
    if (typeof mq.addEventListener === 'function') {
      mq.addEventListener('change', apply)
      return () => mq.removeEventListener('change', apply)
    }
    mq.addListener(apply)
    return () => mq.removeListener(apply)
  }, [])
  return reduce
}

export default function CosmicBackground() {
  const reduceMotion = usePrefersReducedMotion()

  if (reduceMotion) {
    return (
      <div
        className="pointer-events-none fixed inset-0 z-0 bg-black"
        aria-hidden
      />
    )
  }

  return (
    <div className="pointer-events-none fixed inset-0 z-0 bg-black" aria-hidden>
      <Canvas
        camera={{ position: [0, 0, 8.2], fov: 52, near: 0.1, far: 80 }}
        gl={{ alpha: false, antialias: true, powerPreference: 'high-performance' }}
        dpr={[1, 1.5]}
        style={{ width: '100%', height: '100%', display: 'block' }}
      >
        <color attach="background" args={['#000000']} />
        <Scene />
      </Canvas>
    </div>
  )
}
