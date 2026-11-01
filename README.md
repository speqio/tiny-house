# Tiny Houses Autosustentables · Landing 3D

Landing interactiva del proyecto I+D (Academia I+D 2S2026, Facultad de Ingeniería PUCV).
Next.js 15 (App Router) + React 19 + TypeScript + Tailwind 4 + React Three Fiber.

## Comandos

```bash
npm install
npm run dev      # http://localhost:3000
npm run build    # build de producción
npm run lint     # chequeo de tipos
vercel           # preview · vercel --prod para producción
```

## Estructura

- `app/page.tsx` — landing: header, visor 3D, KPIs, pregunta/hipótesis, objetivos, roadmap.
- `components/canvas/Scene.tsx` — Canvas, luces, ambiente, OrbitControls, fly-to, post-procesado (N8AO + Bloom).
- `components/canvas/TinyHouseModel.tsx` — modelo procedural por subsistemas, despiece, plano de corte, rayos X, hotspots.
- `components/ui/*` — panel de control, ficha de hotspot, KPIs y roadmap.
- `lib/*` — estado (zustand), vistas de cámara, hotspots y capas. Los textos y coordenadas se editan aquí.

## Reemplazar el modelo procedural por un GLB

1. Exportar desde Blender/Rhino/FreeCAD a `.glb`, con un nodo raíz por capa:
   `structure`, `solar`, `water`, `envelope`, `interior`.
2. Comprimir: `npx @gltf-transform/cli optimize in.glb public/models/tinyhouse.glb --compress draco`.
3. Cargar con `useGLTF("/models/tinyhouse.glb")` dentro de cada `<Layer>` de `TinyHouseModel.tsx`.

El dossier descargable está en `public/dossier.pdf`.
