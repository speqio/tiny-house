"use client";

import { useEffect, useRef } from "react";
import { animate, motion, useInView } from "framer-motion";
import { Zap, Home, Users, GitBranch } from "lucide-react";

interface Kpi {
  icon: typeof Zap;
  value: number;
  prefix?: string;
  suffix?: string;
  label: string;
  note: string;
  accent: string;
}

const KPIS: Kpi[] = [
  { icon: Zap, value: 40, prefix: "hasta ", suffix: "%", label: "Reducción en boletas de agua y luz", note: "Proyección a validar en piloto", accent: "#eab308" },
  { icon: Home, value: 42000, label: "Solicitudes habitacionales", note: "Región de Valparaíso", accent: "#0284c7" },
  { icon: Users, value: 120000, label: "Familias en campamentos", note: "A nivel nacional", accent: "#10b981" },
  { icon: GitBranch, value: 4, label: "Fases metodológicas", note: "Horizonte de 12–18 meses", accent: "#a78bfa" },
];

// Contador animado al entrar en pantalla
function CountUp({ to }: { to: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!inView || !ref.current) return;
    const node = ref.current;
    const controls = animate(0, to, {
      duration: 1.6,
      ease: "easeOut",
      onUpdate: (v) => (node.textContent = Math.round(v).toLocaleString("es-CL")),
    });
    return () => controls.stop();
  }, [inView, to]);

  return <span ref={ref}>{to.toLocaleString("es-CL")}</span>;
}

// Indicadores de impacto socioambiental
export default function MetricsHUD() {
  return (
    <div className="grid grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4">
      {KPIS.map((k, i) => (
        <motion.div
          key={k.label}
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.08 }}
          className="glass rounded-xl p-3 sm:p-4"
        >
          <k.icon size={16} style={{ color: k.accent }} aria-hidden />
          <p className="mt-2 font-mono text-xl font-semibold text-white sm:text-2xl">
            {k.prefix && <span className="text-sm font-normal text-slate-400">{k.prefix}</span>}
            <CountUp to={k.value} />
            {k.suffix}
          </p>
          <p className="mt-1 text-xs leading-snug text-slate-300 sm:text-sm">{k.label}</p>
          <p className="mt-0.5 text-[11px] text-slate-500">{k.note}</p>
        </motion.div>
      ))}
    </div>
  );
}
