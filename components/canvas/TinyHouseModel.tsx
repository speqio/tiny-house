"use client";

import { useEffect, useMemo, useRef, type ReactNode } from "react";
import { useFrame } from "@react-three/fiber";
import { Html, useGLTF } from "@react-three/drei";
import * as THREE from "three";
import { useViewer, type Axis } from "@/lib/store";
import { SUBSYSTEMS, type LayerId } from "@/lib/subsystems";
import { HOTSPOTS } from "@/lib/hotspots";
import { MATERIAL_TAGS } from "@/lib/materials";

/*
 * Modelo del módulo exportado desde Blender (blender/build_model.py).
 * El GLB trae un nodo raíz por subsistema con los mismos ids de capa, más
 * "terrain"; cada uno se monta en su grupo para despiece, capas y rayos X.
 *
 * Los objetos "cutaway_*" son las piezas del muro frontal que retira el corte;
 * se ocultan para abrir el muro como en el render de referencia.
 *
 * Coordenadas: suelo en y=0, piso del módulo en y=2.25, cubierta en y=5.15,
 * bastidor FV en y≈5.7. Eje X = largo (10,5 m), eje Z = ancho (2,5 m);
 * +Z es el frente (muro en corte y foso del estanque).
 */

const MODEL_URL = "/models/tinyhouse.glb";
const DRACO_URL = "/draco/";
const LAYER_IDS: LayerId[] = ["structure", "envelope", "interior", "solar", "water"];

// Semiextensiones de la escena por eje, para normalizar el plano de corte
const CLIP_EXTENT: Record<Axis, { half: number; center: number }> = {
  x: { half: 7.2, center: 0 },
  y: { half: 4.2, center: 2.3 },
  z: { half: 4.6, center: 0.8 },
};

const CLIP_NORMAL: Record<Axis, THREE.Vector3> = {
  x: new THREE.Vector3(-1, 0, 0),
  y: new THREE.Vector3(0, -1, 0),
  z: new THREE.Vector3(0, 0, -1),
};

// Materiales de las redes de energía y agua: brillo neón para el bloom
const NEON: Record<string, number> = { cable: 1.6, pvc_grey: 1.2, pvc_treated: 1.2 };

// Material compartido de rayos X para las capas que no son redes
const GHOST = new THREE.MeshStandardMaterial({
  color: "#38bdf8",
  transparent: true,
  opacity: 0.12,
  depthWrite: false,
  side: THREE.DoubleSide,
});

interface Prepared {
  terrain: THREE.Object3D;
  layers: Record<LayerId, THREE.Object3D>;
  meshes: { mesh: THREE.Mesh; original: THREE.Material; ghostable: boolean }[];
  cutaway: THREE.Object3D[];
}

// Ajusta materiales y sombras una sola vez tras la carga
function prepare(scene: THREE.Group): Prepared {
  const pick = (name: string) => {
    const node = scene.getObjectByName(name);
    if (!node) throw new Error(`El GLB no contiene el nodo "${name}"`);
    return node;
  };
  const terrain = pick("terrain");
  const layers = Object.fromEntries(LAYER_IDS.map((id) => [id, pick(id)])) as Record<LayerId, THREE.Object3D>;
  const meshes: Prepared["meshes"] = [];
  const cutaway: THREE.Object3D[] = [];
  scene.traverse((o) => {
    if (o.name.startsWith("cutaway_")) cutaway.push(o);
  });

  const collect = (root: THREE.Object3D, ghostable: boolean) =>
    root.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      const m = o.material as THREE.MeshStandardMaterial;
      // los cortes del casco dejan caras visibles por dentro
      m.side = THREE.DoubleSide;
      m.clipShadows = true;
      if (m.transparent) m.depthWrite = false;
      if (m.name in NEON) {
        m.emissive = m.color.clone();
        m.emissiveIntensity = NEON[m.name];
      }
      o.castShadow = !m.transparent;
      o.receiveShadow = true;
      meshes.push({ mesh: o, original: m, ghostable });
    });

  collect(terrain, true);
  // en rayos X, solo las redes de energía y agua quedan sólidas
  for (const id of LAYER_IDS) collect(layers[id], id !== "solar" && id !== "water");
  return { terrain, layers, meshes, cutaway };
}

// Grupo de capa: visibilidad + animación de despiece amortiguada
function Layer({ id, children }: { id: LayerId; children: ReactNode }) {
  const ref = useRef<THREE.Group>(null);
  const visible = useViewer((s) => s.layers[id]);
  const offset = SUBSYSTEMS.find((s) => s.id === id)!.offset;
  const target = useMemo(() => new THREE.Vector3(), []);

  useFrame((_, dt) => {
    if (!ref.current) return;
    const k = useViewer.getState().explode;
    target.set(offset[0] * k, offset[1] * k, offset[2] * k);
    // lerp independiente del framerate
    ref.current.position.lerp(target, 1 - Math.exp(-6 * dt));
  });

  return (
    <group ref={ref} visible={visible}>
      {children}
      <Hotspots layer={id} visible={visible} />
      <MaterialTags layer={id} visible={visible} />
    </group>
  );
}

// Marcadores HTML anclados a la escena
function Hotspots({ layer, visible }: { layer: LayerId; visible: boolean }) {
  const active = useViewer((s) => s.activeHotspot);
  const setHotspot = useViewer((s) => s.setHotspot);
  const setView = useViewer((s) => s.setView);
  if (!visible) return null;

  return (
    <>
      {HOTSPOTS.filter((h) => h.layer === layer).map((h) => (
        <Html key={h.id} position={h.position} center zIndexRange={[20, 0]}>
          <button
            type="button"
            aria-label={`Ver ficha: ${h.title}`}
            onClick={() => {
              setHotspot(h.id);
              setView(h.view);
            }}
            className={`hotspot ${active === h.id ? "hotspot--active" : ""} ${h.future ? "hotspot--future" : ""}`}
          >
            <span className="hotspot__dot" />
            <span className="hotspot__label">{h.title}</span>
          </button>
        </Html>
      ))}
    </>
  );
}

// Rótulos de cada material, anclados a la franja donde queda a la vista en el corte
function MaterialTags({ layer, visible }: { layer: LayerId; visible: boolean }) {
  const show = useViewer((s) => s.cutaway && s.materialTags);
  if (!visible || !show) return null;

  return (
    <>
      {MATERIAL_TAGS.filter((t) => t.layer === layer).map((t) => (
        <Html key={t.id} position={t.position} zIndexRange={[15, 0]}>
          <span className="mtag">
            <span className="mtag__dot" />
            <span className="mtag__label">{t.label}</span>
          </span>
        </Html>
      ))}
    </>
  );
}

export default function TinyHouseModel() {
  const { scene } = useGLTF(MODEL_URL, DRACO_URL);
  const parts = useMemo(() => prepare(scene), [scene]);
  const mode = useViewer((s) => s.mode);
  const clipAxis = useViewer((s) => s.clipAxis);
  const clipPos = useViewer((s) => s.clipPos);
  const cutaway = useViewer((s) => s.cutaway);

  // plano de corte compartido por todos los materiales
  const plane = useMemo(() => new THREE.Plane(), []);
  const { half, center } = CLIP_EXTENT[clipAxis];
  plane.normal.copy(CLIP_NORMAL[clipAxis]);
  plane.constant = center + clipPos * half;

  useEffect(() => {
    const planes = mode === "section" ? [plane] : [];
    const xray = mode === "xray";
    GHOST.clippingPlanes = planes;
    for (const { mesh, original, ghostable } of parts.meshes) {
      original.clippingPlanes = planes;
      original.needsUpdate = true;
      mesh.material = xray && ghostable ? GHOST : original;
      mesh.castShadow = !(xray && ghostable) && !original.transparent;
    }
    GHOST.needsUpdate = true;
  }, [mode, parts, plane]);

  useEffect(() => {
    for (const o of parts.cutaway) o.visible = !cutaway;
  }, [cutaway, parts]);

  return (
    <group>
      <primitive object={parts.terrain} />
      {LAYER_IDS.map((id) => (
        <Layer key={id} id={id}>
          <primitive object={parts.layers[id]} />
        </Layer>
      ))}
    </group>
  );
}

useGLTF.preload(MODEL_URL, DRACO_URL);
