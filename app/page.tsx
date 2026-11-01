import { Download, Droplets, Sun, Building2, HelpCircle, FlaskConical, Target } from "lucide-react";
import ViewerClient from "@/components/canvas/ViewerClient";
import ControlsOverlay from "@/components/ui/ControlsOverlay";
import HotspotCard from "@/components/ui/HotspotCard";
import MetricsHUD from "@/components/ui/MetricsHUD";
import Roadmap from "@/components/ui/Roadmap";

const OBJECTIVES = [
  "Caracterizar el déficit habitacional y la pobreza hídrica/energética en Valparaíso.",
  "Diseñar y dimensionar el módulo y sus subsistemas fotovoltaico y de aguas grises.",
  "Desarrollar un prototipo instrumentado a escala.",
  "Estimar el impacto económico, social y ambiental frente al modelo estándar.",
  "Definir una ruta de escalamiento hacia financiamiento e implementación.",
];

const PILLARS = [
  { icon: Building2, title: "Diseño modular", body: "Estructura prefabricada en taller: menos tiempo de obra y menor impacto ambiental.", color: "text-slate-300" },
  { icon: Sun, title: "Energía solar", body: "Arreglo fotovoltaico que reduce la dependencia de la red y la boleta eléctrica.", color: "text-yellow-400" },
  { icon: Droplets, title: "Aguas grises", body: "Tratamiento y reúso del agua de duchas y lavamanos para inodoros y riego.", color: "text-sky-400" },
];

export default function Home() {
  return (
    <main>
      {/* Header */}
      <header className="glass fixed inset-x-0 top-0 z-30 flex h-14 items-center justify-between gap-3 px-3 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <span className="font-mono text-sm font-semibold text-white">
            TinyHouse <span className="text-emerald-400">I+D</span>
          </span>
          <span className="hidden truncate text-xs text-slate-400 md:inline">PUCV · Facultad de Ingeniería</span>
        </div>
        <div className="flex items-center gap-2">
          <a
            href="#trl"
            title="Madurez tecnológica actual y meta del proyecto"
            className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2.5 py-1 font-mono text-[11px] text-emerald-300 hover:bg-emerald-500/20"
          >
            TRL 2 → 4-5
          </a>
          <a
            href="/dossier.pdf"
            download
            className="flex items-center gap-1.5 rounded-lg bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-500"
          >
            <Download size={14} aria-hidden />
            <span className="hidden sm:inline">Dossier de investigación (PDF)</span>
            <span className="sm:hidden">Dossier</span>
          </a>
        </div>
      </header>

      {/* Visor 3D a pantalla completa con HUD superpuesto */}
      <section className="relative h-[100svh] min-h-[560px] w-full" aria-label="Visor 3D">
        <ViewerClient />
        <ControlsOverlay />
        <HotspotCard />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-[#090d16] via-[#090d16]/70 to-transparent px-3 pb-4 pt-16 sm:px-6">
          <div className="pointer-events-auto mx-auto max-w-6xl">
            <h1 className="mb-3 max-w-3xl text-lg font-semibold leading-tight text-white sm:text-2xl">
              Tiny Houses Autosustentables
              <span className="block text-sm font-normal text-slate-400 sm:text-base">
                Vivienda social modular con eficiencia hídrica y energía solar fotovoltaica · Región de Valparaíso
              </span>
            </h1>
            <MetricsHUD />
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl space-y-20 px-4 py-20 sm:px-6">
        {/* Problema e hipótesis */}
        <section className="grid gap-4 md:grid-cols-2">
          <div className="glass rounded-xl p-6">
            <HelpCircle className="text-sky-400" size={20} aria-hidden />
            <h2 className="mt-3 font-semibold text-white">Pregunta de investigación</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-300">
              ¿En qué medida un modelo de vivienda social modular con generación fotovoltaica y reutilización de aguas
              grises reduce los costos de habitabilidad y la pobreza energética de familias vulnerables de la Región de
              Valparaíso, frente al modelo estándar?
            </p>
          </div>
          <div className="glass rounded-xl p-6">
            <FlaskConical className="text-emerald-400" size={20} aria-hidden />
            <h2 className="mt-3 font-semibold text-white">Hipótesis de trabajo</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-300">
              Un módulo prefabricado con paneles solares y tratamiento de aguas grises reduce significativamente los
              costos mensuales de agua y electricidad, sin aumentar sustancialmente el costo ni el tiempo de
              construcción. La reducción del 40% es una <strong className="text-white">proyección preliminar a validar</strong> en el piloto instrumentado.
            </p>
          </div>
        </section>

        {/* Propuesta técnica */}
        <section>
          <h2 className="text-xl font-semibold text-white">Propuesta técnica</h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-400">
            Existe evidencia sólida para cada subsistema por separado; el aporte del proyecto es integrarlos en un único
            módulo para vivienda social.
          </p>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {PILLARS.map((p) => (
              <div key={p.title} className="glass rounded-xl p-5">
                <p.icon className={p.color} size={20} aria-hidden />
                <h3 className="mt-3 font-semibold text-white">{p.title}</h3>
                <p className="mt-1.5 text-sm text-slate-300">{p.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Objetivos */}
        <section>
          <h2 className="flex items-center gap-2 text-xl font-semibold text-white">
            <Target size={20} className="text-yellow-400" aria-hidden /> Objetivos específicos
          </h2>
          <ol className="mt-6 grid gap-3 md:grid-cols-5">
            {OBJECTIVES.map((o, i) => (
              <li key={o} className="glass rounded-xl p-4 text-sm text-slate-300">
                <span className="font-mono text-xs text-sky-400">OE{i + 1}</span>
                <p className="mt-1">{o}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Roadmap */}
        <section id="trl" className="scroll-mt-20">
          <h2 className="text-xl font-semibold text-white">Roadmap · 4 fases metodológicas</h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-400">
            Hoy en TRL 2 (concepto formulado, escala KTH). Meta: TRL 4-5 con el prototipo instrumentado y el piloto en
            terreno.
          </p>
          <div className="mt-8">
            <Roadmap />
          </div>
        </section>
      </div>

      <footer className="border-t border-white/10 px-4 py-8 text-center text-xs text-slate-500">
        Francesco Eduardo Mori Rojas · Academia I+D 2S2026 · Facultad de Ingeniería PUCV · Profesor/a patrocinante: [a completar]
      </footer>
    </main>
  );
}
