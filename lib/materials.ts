import type { LayerId } from "./subsystems";

// Etiquetas de materiales visibles en el corte frontal (coordenadas de escena).
// Cada capa del muro se retira con un retranqueo distinto, así que cada
// etiqueta apunta a la franja donde ese material queda a la vista.
export interface MaterialTag {
  id: string;
  label: string;
  layer: LayerId;
  position: [number, number, number];
}

export const MATERIAL_TAGS: MaterialTag[] = [
  { id: "skin", label: "Chapa de acero del casco reciclado", layer: "envelope", position: [-4.85, 3.75, 1.27] },
  { id: "wool", label: "Lana mineral en placas, 150 mm", layer: "envelope", position: [-4.56, 3.35, 1.22] },
  { id: "studs", label: "Bastidor de madera 45 × 150 mm @ 60 cm", layer: "envelope", position: [1.7, 2.53, 1.22] },
  { id: "lining", label: "Placa interior 15 mm", layer: "envelope", position: [-2.6, 2.71, 1.07] },
  { id: "roof", label: "Cubierta: chapa + lana mineral", layer: "envelope", position: [0.6, 5.05, 1.05] },
  { id: "floor", label: "Piso de madera sobre placas de lana", layer: "interior", position: [-0.6, 2.48, 0.85] },
  { id: "cells", label: "Bastidor de cajones de plancha de acero", layer: "structure", position: [-3.0, 2.02, 1.2] },
  { id: "beam", label: "Viga I 300 mm sobre pilares H", layer: "structure", position: [-3.6, 1.65, 1.15] },
];
