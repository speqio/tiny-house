// Capas / subsistemas del módulo y su desplazamiento en la vista explosionada
export type LayerId = "structure" | "solar" | "water" | "envelope" | "interior";

export interface Subsystem {
  id: LayerId;
  label: string;
  color: string;
  // vector de separación (unidades de escena) a explode = 1
  offset: [number, number, number];
}

export const SUBSYSTEMS: Subsystem[] = [
  { id: "structure", label: "Estructura metálica y fundaciones", color: "#94a3b8", offset: [0, -1.6, 0] },
  { id: "solar", label: "Subsistema fotovoltaico", color: "#eab308", offset: [0, 3.2, 0] },
  { id: "water", label: "Subsistema de aguas grises", color: "#38bdf8", offset: [0, -0.6, 3.2] },
  { id: "envelope", label: "Envolvente y aislación", color: "#f59e0b", offset: [0, 1.2, -2.4] },
  { id: "interior", label: "Mobiliario interior", color: "#10b981", offset: [0, 0.4, 1.4] },
];
