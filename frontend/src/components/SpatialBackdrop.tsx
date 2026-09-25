import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useMemo, useRef } from "react";
import * as THREE from "three";

function ParticleField() {
  const points = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const values = new Float32Array(420 * 3);
    for (let index = 0; index < 420; index += 1) {
      const radius = 3.5 + Math.random() * 4;
      const angle = Math.random() * Math.PI * 2;
      values[index * 3] = Math.cos(angle) * radius;
      values[index * 3 + 1] = (Math.random() - 0.5) * 5;
      values[index * 3 + 2] = Math.sin(angle) * radius - 2;
    }
    return values;
  }, []);

  useFrame((_, delta) => {
    if (!points.current) return;
    points.current.rotation.y += delta * 0.018;
    points.current.rotation.x = Math.sin(Date.now() * 0.00012) * 0.06;
  });

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} count={positions.length / 3} />
      </bufferGeometry>
      <pointsMaterial color="#73c8c8" size={0.018} transparent opacity={0.55} sizeAttenuation />
    </points>
  );
}

function OrbitCore() {
  const group = useRef<THREE.Group>(null);
  useFrame((_, delta) => {
    if (!group.current) return;
    group.current.rotation.z += delta * 0.12;
    group.current.rotation.y -= delta * 0.08;
  });
  return (
    <group ref={group} position={[0, 0, -2.5]}>
      <mesh>
        <icosahedronGeometry args={[0.65, 2]} />
        <meshBasicMaterial color="#1b5961" wireframe transparent opacity={0.17} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.95, 0.008, 8, 96]} />
        <meshBasicMaterial color="#91d7cb" transparent opacity={0.24} />
      </mesh>
    </group>
  );
}

export default function SpatialBackdrop() {
  return (
    <div className="spatial-backdrop" aria-hidden="true">
      <Canvas camera={{ position: [0, 0, 6], fov: 45 }} dpr={[1, 1.25]} gl={{ antialias: true, alpha: true }}>
        <ParticleField />
        <OrbitCore />
        <OrbitControls enableZoom={false} enablePan={false} enableRotate={false} />
      </Canvas>
    </div>
  );
}
