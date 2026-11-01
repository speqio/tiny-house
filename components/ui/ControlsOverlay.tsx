"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Box, Layers, Scissors, ScanEye, SlidersHorizontal, Camera, ChevronLeft } from "lucide-react";
import { useViewer, type RenderMode, type Axis } from "@/lib/store";
import { SUBSYSTEMS } from "@/lib/subsystems";
import { VIEWS } from "@/lib/views";

const MODES: { id: RenderMode; label: string; icon: typeof Box }[] = [
  { id: "full", label: "Completo", icon: Box },
  { id: "exploded", label: "Explosionado", icon: Layers },
  { id: "section", label: "Corte", icon: Scissors },
  { id: "xray", label: "Rayos X", icon: ScanEye },
];

// Panel lateral flotante con todos los controles del visor
export default function ControlsOverlay() {
  const [open, setOpen] = useState(true);
  const s = useViewer();

  return (
    <div className="pointer-events-none absolute left-3 top-20 z-20 flex max-h-[calc(100%-6rem)] items-start sm:left-4">
      <AnimatePresence initial={false}>
        {open && (
          <motion.aside
            initial={{ opacity: 0, x: -16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -16 }}
            className="glass pointer-events-auto w-[17rem] max-h-full overflow-y-auto rounded-xl p-4 text-sm"
            aria-label="Panel de control 3D"
          >
            <Section icon={SlidersHorizontal} title="Renderizado">
              <div className="grid grid-cols-2 gap-1.5">
                {MODES.map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => s.setMode(id)}
                    aria-pressed={s.mode === id}
                    className={`chip ${s.mode === id ? "chip--on" : ""}`}
                  >
                    <Icon size={14} aria-hidden /> {label}
                  </button>
                ))}
              </div>

              <label className="mt-3 block text-xs text-slate-400">
                Despiece · {Math.round(s.explode * 100)}%
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={s.explode}
                  onChange={(e) => s.setExplode(Number(e.target.value))}
                  className="range mt-1"
                />
              </label>

              <label className="mt-3 flex cursor-pointer items-center gap-2 text-slate-200">
                <input
                  type="checkbox"
                  checked={s.cutaway}
                  onChange={(e) => s.setCutaway(e.target.checked)}
                  className="h-4 w-4 accent-sky-600"
                />
                Muro frontal en corte
              </label>
              <label className={`mt-1.5 flex items-center gap-2 ${s.cutaway ? "cursor-pointer text-slate-200" : "text-slate-500"}`}>
                <input
                  type="checkbox"
                  checked={s.materialTags}
                  disabled={!s.cutaway}
                  onChange={(e) => s.setMaterialTags(e.target.checked)}
                  className="h-4 w-4 accent-sky-600"
                />
                Etiquetas de materiales
              </label>

              {s.mode === "section" && (
                <div className="mt-3">
                  <div className="flex gap-1.5" role="group" aria-label="Eje del plano de corte">
                    {(["x", "y", "z"] as Axis[]).map((a) => (
                      <button
                        key={a}
                        type="button"
                        onClick={() => s.setClipAxis(a)}
                        aria-pressed={s.clipAxis === a}
                        className={`chip flex-1 justify-center uppercase ${s.clipAxis === a ? "chip--on" : ""}`}
                      >
                        {a}
                      </button>
                    ))}
                  </div>
                  <label className="mt-2 block text-xs text-slate-400">
                    Posición del plano
                    <input
                      type="range"
                      min={-1}
                      max={1}
                      step={0.01}
                      value={s.clipPos}
                      onChange={(e) => s.setClipPos(Number(e.target.value))}
                      className="range mt-1"
                    />
                  </label>
                </div>
              )}
            </Section>

            <Section icon={Camera} title="Vistas de ingeniería">
              <div className="flex flex-col gap-1">
                {VIEWS.map((v) => (
                  <button
                    key={v.id}
                    type="button"
                    onClick={() => s.setView(v.id)}
                    aria-pressed={s.view === v.id}
                    className={`chip ${s.view === v.id ? "chip--on" : ""}`}
                  >
                    {v.label}
                  </button>
                ))}
              </div>
            </Section>

            <Section icon={Layers} title="Capas / subsistemas">
              <ul className="flex flex-col gap-1.5">
                {SUBSYSTEMS.map((sub) => (
                  <li key={sub.id}>
                    <label className="flex cursor-pointer items-center gap-2 text-slate-200">
                      <input
                        type="checkbox"
                        checked={s.layers[sub.id]}
                        onChange={() => s.toggleLayer(sub.id)}
                        className="h-4 w-4 accent-sky-600"
                      />
                      <span className="h-2.5 w-2.5 rounded-full" style={{ background: sub.color, boxShadow: `0 0 8px ${sub.color}` }} />
                      {sub.label}
                    </label>
                  </li>
                ))}
              </ul>
            </Section>
          </motion.aside>
        )}
      </AnimatePresence>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Ocultar panel de control" : "Mostrar panel de control"}
        aria-expanded={open}
        className="glass pointer-events-auto ml-2 rounded-lg p-2 text-slate-300 hover:text-white"
      >
        <ChevronLeft size={16} className={open ? "" : "rotate-180"} />
      </button>
    </div>
  );
}

function Section({ icon: Icon, title, children }: { icon: typeof Box; title: string; children: React.ReactNode }) {
  return (
    <section className="mb-4 last:mb-0">
      <h2 className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        <Icon size={13} aria-hidden /> {title}
      </h2>
      {children}
    </section>
  );
}
