"use client";

import { motion } from "framer-motion";

interface Phase {
  n: number;
  title: string;
  body: string;
  funding?: string;
  trl: string;
}

const PHASES: Phase[] = [
  {
    n: 1,
    title: "Diseño y validación técnica",
    body: "Revisión sistemática, línea base regional y dimensionamiento con modelamiento paramétrico (PVsyst o análogo, balances de masa del subsistema hídrico).",
    funding: "Fondos internos Academia I+D",
    trl: "TRL 2 → 3",
  },
  {
    n: 2,
    title: "Prototipado instrumentado",
    body: "Módulo de prueba con medidores de consumo eléctrico, caudalímetros y sondas de calidad de agua, en ciclos build–measure–learn.",
    funding: "Semilla Inicia CORFO · $15–17M CLP",
    trl: "TRL 3 → 4",
  },
  {
    n: 3,
    title: "Piloto en terreno",
    body: "Instalación en un caso real o simulado de Valparaíso con monitoreo continuo de al menos 12 semanas y co-diseño con la familia beneficiaria.",
    trl: "TRL 4 → 5",
  },
  {
    n: 4,
    title: "Escalamiento",
    body: "Análisis estadístico, ajuste del modelo técnico-económico y postulación a instrumentos de mayor escala.",
    funding: "IDeA I+D ANID/FONDEF 2027 · hasta $227,7M CLP / 24 meses",
    trl: "Meta TRL 4–5",
  },
];

// Línea de tiempo de las 4 fases metodológicas
export default function Roadmap() {
  return (
    <ol className="relative grid gap-4 md:grid-cols-4">
      {/* línea conectora */}
      <div aria-hidden className="absolute left-4 top-4 hidden h-px w-[calc(100%-2rem)] bg-gradient-to-r from-sky-600 via-emerald-500 to-yellow-500 md:block" />
      {PHASES.map((p, i) => (
        <motion.li
          key={p.n}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.1 }}
          className="relative"
        >
          <span className="relative z-10 flex h-8 w-8 items-center justify-center rounded-full border border-sky-500/60 bg-[#090d16] font-mono text-sm text-sky-300">
            {p.n}
          </span>
          <div className="glass mt-3 rounded-xl p-4">
            <p className="font-mono text-[11px] uppercase tracking-wider text-emerald-400">{p.trl}</p>
            <h3 className="mt-1 font-semibold text-white">{p.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-300">{p.body}</p>
            {p.funding && <p className="mt-3 text-xs font-medium text-yellow-400">{p.funding}</p>}
          </div>
        </motion.li>
      ))}
    </ol>
  );
}
