"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Activity } from "lucide-react";
import { useViewer } from "@/lib/store";
import { HOTSPOTS } from "@/lib/hotspots";

// Ficha técnica del hotspot activo
export default function HotspotCard() {
  const id = useViewer((s) => s.activeHotspot);
  const setHotspot = useViewer((s) => s.setHotspot);
  const h = HOTSPOTS.find((x) => x.id === id);

  return (
    <AnimatePresence>
      {h && (
        <motion.div
          key={h.id}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 12 }}
          role="dialog"
          aria-label={h.title}
          className="glass absolute right-3 top-20 z-20 w-[min(20rem,calc(100%-1.5rem))] rounded-xl p-4 sm:right-4"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              {h.future && <span className="mb-1 inline-block rounded bg-slate-700 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-slate-300">Futuro · 2ª etapa</span>}
              <h3 className="font-semibold text-white">{h.title}</h3>
            </div>
            <button type="button" onClick={() => setHotspot(null)} aria-label="Cerrar ficha" className="text-slate-400 hover:text-white">
              <X size={16} />
            </button>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-slate-300">{h.body}</p>
          {h.instrumentation && (
            <div className="mt-3 border-t border-white/10 pt-3">
              <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-emerald-400">
                <Activity size={12} aria-hidden /> Instrumentación prevista
              </p>
              <ul className="space-y-0.5 text-xs text-slate-300">
                {h.instrumentation.map((v) => (
                  <li key={v}>· {v}</li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
