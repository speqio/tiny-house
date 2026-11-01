import type { ViewId } from "./views";
import type { LayerId } from "./subsystems";

// Fichas técnicas ancladas a coordenadas 3D de la escena
export interface Hotspot {
  id: string;
  title: string;
  layer: LayerId;
  position: [number, number, number];
  view: ViewId;
  body: string;
  instrumentation?: string[]; // variables medibles del Perfil I+D
  future?: boolean; // ampliación 2ª etapa (no parte del prototipo)
}

export const HOTSPOTS: Hotspot[] = [
  {
    id: "pv",
    title: "Generación fotovoltaica",
    layer: "solar",
    position: [0, 6.2, 0],
    view: "solar",
    body: "Arreglo de 20 paneles de 150 W (3.000 W) sobre bastidor metálico independiente, con inversor en el tabique técnico. Reducción proyectada de hasta 40% en boletas de agua y electricidad, cifra a validar en el piloto.",
    instrumentation: ["Generación FV (kWh/día)", "Consumo eléctrico residual (kWh/mes)"],
  },
  {
    id: "greywater",
    title: "Ahorro hídrico",
    layer: "water",
    position: [2.0, 0.4, 2.9],
    view: "water",
    body: "Reutilización de aguas de duchas y lavamanos para inodoros y riego: colector, biofiltro de grava/arena, estanque acumulador de 1.000 L y bomba.",
    instrumentation: ["Caudal tratado (L/día)", "Calidad: DBO, turbidez, coliformes", "Agua potable residual (L/mes)"],
  },
  {
    id: "structure",
    title: "Estructura prefabricada",
    layer: "structure",
    position: [-4.8, 1.0, 1.1],
    view: "structure",
    body: "Casco de trolebús reciclado sobre bastidor de cajones de acero, vigas I y 10 pilares H de 1,50 m en dados de hormigón: montaje modular de bajo impacto y mínimo movimiento de tierra.",
    instrumentation: ["Tiempo de ejecución constructiva (días)"],
  },
  {
    id: "thermal",
    title: "Confort térmico",
    layer: "envelope",
    position: [-4.56, 4.3, 1.22],
    view: "interior",
    body: "Envolvente con aislación continua conforme a la normativa térmica MINVU, orientada a reducir la pobreza energética.",
    instrumentation: ["Temperatura interior (°C)", "Humedad relativa (% HR)"],
  },
  {
    id: "future",
    title: "Ampliación 2ª etapa",
    layer: "solar",
    position: [4.6, 5.9, -1.0],
    view: "iso",
    body: "Líneas futuras fuera del alcance del prototipo: turbina eólica de eje vertical, captación de agua lluvia y sistema de biogás.",
    future: true,
  },
];
