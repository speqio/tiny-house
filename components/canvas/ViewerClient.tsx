"use client";

import dynamic from "next/dynamic";

// WebGL solo existe en el navegador: se desactiva el SSR del Canvas
const Scene = dynamic(() => import("./Scene"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center text-sm text-slate-400">
      Cargando modelo 3D…
    </div>
  ),
});

export default function ViewerClient() {
  return <Scene />;
}
