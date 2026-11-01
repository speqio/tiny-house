// Vistas predefinidas de ingeniería: posición de cámara y punto objetivo
export type ViewId = "iso" | "structure" | "solar" | "water" | "interior";

export interface CameraView {
  id: ViewId;
  label: string;
  position: [number, number, number];
  target: [number, number, number];
}

export const VIEWS: CameraView[] = [
  { id: "iso", label: "Isométrica general", position: [14, 9, 15], target: [0, 2.4, 0.4] },
  { id: "structure", label: "Estructura / cimentación", position: [10, 2, 10], target: [0, 0.9, 0] },
  { id: "solar", label: "Subsistema fotovoltaico", position: [5, 12, 8], target: [0, 5.5, 0] },
  { id: "water", label: "Subsistema hídrico", position: [7, 2.5, 10], target: [1.4, 0, 2.2] },
  { id: "interior", label: "Interior / confort térmico", position: [1.5, 4.1, 8], target: [-0.5, 3.1, 0] },
];

export const getView = (id: ViewId): CameraView =>
  VIEWS.find((v) => v.id === id) ?? VIEWS[0];
