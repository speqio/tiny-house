# Especificación del modelo 3D (Blender → GLB)

**Fuente de verdad de los parámetros:** [`reference_spec.json`](reference_spec.json), con la lectura de la imagen de
referencia y los datos del autor; cada valor indica si viene de `autor`, `imagen` o `supuesto`. `build_model.py` lo lee al
iniciar. Este documento resume las decisiones.

Unidades: metros. Eje X = largo del módulo, Z (Blender) = altura. Suelo en cota 0.
Cada subsistema va en una colección / nodo raíz con estos nombres exactos (los usa el visor):
`structure`, `solar`, `water`, `envelope`, `interior`.

## Datos entregados por el autor
| Elemento | Valor |
|---|---|
| Casco | Trolebús reciclado (referencia: trolebuses patrimoniales de Valparaíso) |
| Pilotes | 10 pilotes de acero, altura libre 1,50 m (2 filas × 5) |
| Panel FV | 1,16 × 0,65 m · espesor indicado 18 cm (**por confirmar**, ver nota) |
| Potencia FV | 3.000 W totales |
| Estanque acumulador | 1.000 L |

## Supuestos (parametrizables en `build_model.py`)
- Casco: 10,5 × 2,5 m en planta, 2,9 m de alto exterior. **Supuesto, a reemplazar por las medidas reales.**
- Pilotes: separación aprox. 2,4 m en el largo y 2,2 m en el ancho; zapata de hormigón de 0,6 × 0,6 × 0,4 m.
- Arreglo FV: 20 paneles de 150 W = 3.000 W, en 2 filas × 10 (lado de 1,16 m en el ancho).
- Espesor del panel: el valor indicado (18 cm) no es habitual; se modela con 3,5 cm hasta confirmarlo.
- Estanque: caja de vidrio de 1,40 × 1,00 × 0,75 m (≈1,05 m³ bruto) en foso, más la bomba.
- Aislación de lana mineral en placas de 0,6 × 0,4 m entre perfiles: 100 mm en muro, cubierta y piso. Pensada para la zona térmica de
  Valparaíso según la OGUC 4.1.10; **falta verificar el cálculo de transmitancia U**.

## Composición (según imagen de referencia)
- Frente (-Y en Blender, +Z en el visor): corte escalonado. La chapa se retira 35 cm más que el revestimiento y la capa
  de bastidor de madera + lana 18 cm, de modo que quedan a la vista chapa, bastidor de madera @ 60 cm con placas de lana y placa interior.
  Las piezas retiradas se exportan como `cutaway_*`; el visor las oculta o muestra (opción "Muro frontal en corte").
- Soporte: pilares de perfil H sobre dados de hormigón únicos, vigas I longitudinales de 300 mm y encima un bastidor
  de cajones de plancha de acero (450 mm) bajo casco y terraza; su plancha frontal es `cutaway_chassis_front`.
- Acceso: antigua puerta de pasajeros (plegable) en el costado +Y junto al extremo trasero; descanso en ménsula y
  escalera de 9 peldaños paralela al costado.
- Recintos amoblados: cocina-comedor (-X), dormitorio con escritorio, closet técnico (inversor, tablero, datalogger,
  batería), baño con azulejos, ducha vidriada, inodoro y vanitorio, y hall hacia la terraza.
- Bastidor FV independiente, 0,55 m sobre la cubierta, con arriostramiento en X.
- Biofiltro en jardinera de hormigón con plantas bajo el casco; estanque en foso con muros de hormigón.

## Materiales PBR (CC0, ambientCG / Poly Haven)
Casco: pintura metálica envejecida, azul y amarillo con óxido · Acero estructural galvanizado · Hormigón ·
Madera de terraza · Lana mineral (amarillo) · Grava, arena y tierra vegetal del biofiltro · Vidrio ·
PVC celeste (aguas grises) y verde (agua tratada) · Cableado amarillo.

Texturas usadas (1K, en `blender/textures/`): PaintedMetal006 (recoloreada a amarillo y azul por
`generate_textures.py`), PaintedMetal013 (cubierta), Metal032, Concrete034, Planks037A, WoodFloor051,
Grass004, Ground048, Ground054, Gravel023. Las celdas FV también se generan en `generate_textures.py`.

## Salida
`public/models/tinyhouse.glb` (Draco + texturas WebP), ~5,4 MB. Decodificador Draco servido desde `public/draco/`.
