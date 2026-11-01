"use client";

import { create } from "zustand";
import type { LayerId } from "./subsystems";
import type { ViewId } from "./views";

// Modos de renderizado del visor
export type RenderMode = "full" | "exploded" | "section" | "xray";
export type Axis = "x" | "y" | "z";

interface ViewerState {
  mode: RenderMode;
  explode: number; // 0 = ensamblado, 1 = despiece completo
  clipAxis: Axis;
  clipPos: number; // posición normalizada -1..1
  cutaway: boolean; // muro frontal abierto, como en el render de referencia
  materialTags: boolean;
  layers: Record<LayerId, boolean>;
  view: ViewId;
  viewNonce: number; // fuerza re-disparo del fly-to aunque se repita la vista
  activeHotspot: string | null;
  setMode: (m: RenderMode) => void;
  setExplode: (v: number) => void;
  setClipAxis: (a: Axis) => void;
  setClipPos: (v: number) => void;
  setCutaway: (v: boolean) => void;
  setMaterialTags: (v: boolean) => void;
  toggleLayer: (id: LayerId) => void;
  setView: (v: ViewId) => void;
  setHotspot: (id: string | null) => void;
}

export const useViewer = create<ViewerState>((set) => ({
  mode: "full",
  explode: 0,
  clipAxis: "x",
  clipPos: 0.2,
  cutaway: true,
  materialTags: false,
  layers: {
    structure: true,
    solar: true,
    water: true,
    envelope: true,
    interior: true,
  },
  view: "iso",
  viewNonce: 0,
  activeHotspot: null,
  setMode: (mode) =>
    set((s) => ({
      mode,
      // al entrar/salir de despiece se ajusta el slider automáticamente
      explode: mode === "exploded" ? (s.explode > 0 ? s.explode : 0.7) : 0,
    })),
  setExplode: (explode) =>
    set({ explode, mode: explode > 0 ? "exploded" : "full" }),
  setClipAxis: (clipAxis) => set({ clipAxis }),
  setClipPos: (clipPos) => set({ clipPos }),
  setCutaway: (cutaway) => set({ cutaway }),
  setMaterialTags: (materialTags) => set({ materialTags }),
  toggleLayer: (id) =>
    set((s) => ({ layers: { ...s.layers, [id]: !s.layers[id] } })),
  setView: (view) => set((s) => ({ view, viewNonce: s.viewNonce + 1 })),
  setHotspot: (activeHotspot) => set({ activeHotspot }),
}));
