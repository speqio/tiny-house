"use client";

import { Suspense, useEffect, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Lightformer, OrbitControls } from "@react-three/drei";
import { EffectComposer, Bloom, N8AO } from "@react-three/postprocessing";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import TinyHouseModel from "./TinyHouseModel";
import { useViewer } from "@/lib/store";
import { getView } from "@/lib/views";

// Transición fly-to: interpola cámara y objetivo hacia la vista seleccionada
function CameraRig() {
  const camera = useThree((s) => s.camera);
  const controls = useThree((s) => s.controls) as OrbitControlsImpl | null;
  const nonce = useViewer((s) => s.viewNonce);
  const view = useViewer((s) => s.view);
  const flying = useRef(false);
  const goalPos = useRef(new THREE.Vector3());
  const goalTarget = useRef(new THREE.Vector3());

  useEffect(() => {
    const v = getView(view);
    goalPos.current.set(...v.position);
    goalTarget.current.set(...v.target);
    flying.current = true;
  }, [nonce, view]);

  // el usuario retoma el control si arrastra durante la transición
  useEffect(() => {
    if (!controls) return;
    const stop = () => (flying.current = false);
    controls.addEventListener("start", stop);
    return () => controls.removeEventListener("start", stop);
  }, [controls]);

  useFrame((_, dt) => {
    if (!flying.current || !controls) return;
    const k = 1 - Math.exp(-3.5 * dt);
    camera.position.lerp(goalPos.current, k);
    controls.target.lerp(goalTarget.current, k);
    controls.update();
    if (
      camera.position.distanceTo(goalPos.current) < 0.02 &&
      controls.target.distanceTo(goalTarget.current) < 0.02
    ) {
      flying.current = false;
    }
  });

  return null;
}

export default function Scene() {
  const iso = getView("iso");
  const setHotspot = useViewer((s) => s.setHotspot);

  return (
    <Canvas
      shadows
      dpr={[1, 2]}
      camera={{ position: iso.position, fov: 38, near: 0.1, far: 200 }}
      gl={{ localClippingEnabled: true, antialias: true }}
      onPointerMissed={() => setHotspot(null)}
      aria-label="Modelo 3D interactivo del módulo Tiny House"
    >
      <color attach="background" args={["#090d16"]} />
      <fog attach="fog" args={["#090d16", 28, 60]} />

      <ambientLight intensity={0.35} />
      <directionalLight
        position={[8, 14, 6]}
        intensity={2.2}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-12}
        shadow-camera-right={12}
        shadow-camera-top={12}
        shadow-camera-bottom={-12}
        shadow-bias={-0.0004}
      />

      <Suspense fallback={null}>
        <TinyHouseModel />
        {/* ambiente PBR generado localmente, sin descargar HDRI */}
        <Environment resolution={256}>
          <Lightformer intensity={2} position={[0, 6, 0]} rotation-x={Math.PI / 2} scale={[12, 12, 1]} />
          <Lightformer intensity={1.2} color="#0284c7" position={[-8, 2, 4]} scale={[6, 3, 1]} />
          <Lightformer intensity={0.8} color="#eab308" position={[8, 2, -4]} scale={[6, 3, 1]} />
        </Environment>
      </Suspense>

      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.08}
        minDistance={4}
        maxDistance={34}
        maxPolarAngle={Math.PI * 0.55}
        target={iso.target}
      />
      <CameraRig />

      <EffectComposer multisampling={0}>
        <N8AO aoRadius={0.8} intensity={2.5} distanceFalloff={0.6} halfRes />
        <Bloom intensity={0.6} luminanceThreshold={0.85} luminanceSmoothing={0.2} mipmapBlur />
      </EffectComposer>
    </Canvas>
  );
}
