"""Construye el modelo de la Tiny House en Blender y lo exporta a GLB.

Ejecutar vía MCP:  python blender/mcp_client.py exec blender/build_model.py
Antes, generar las texturas derivadas:  python blender/generate_textures.py
Unidades en metros, Z arriba (el exportador glTF convierte a Y arriba:
Blender (x, y, z) -> three (x, z, -y)). Ver blender/SPEC.md.

Los parámetros vienen de blender/reference_spec.json (lectura de la imagen de
referencia + datos del autor).

Orientación: -Y es el frente (muro en corte, foso del estanque), +X la terraza,
-X la puerta trasera con descanso y escalera. Las piezas del muro frontal que
retira el corte se exportan como objetos "cutaway_*" para que el visor pueda
abrir o cerrar el corte.
"""

import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

# ---------------------------------------------------------------- parámetros
SPEC = json.load(open(r"C:\Users\paolin\Desktop\DEPLOII\TINIHOUSE\blender\reference_spec.json", encoding="utf-8"))
_h, _e, _s = SPEC["hull"], SPEC["envelope"], SPEC["structure"]
HULL_L, HULL_W, HULL_H = _h["length"]["value"], _h["width"]["value"], _h["height"]["value"]
HULL_R = _h["corner_radius"]["value"]
PILE_H = _s["piles"]["free_height"]["value"]
PILE_XS = _s["piles"]["grid_x"]
PILE_YS = _s["piles"]["grid_y"]
PILE_SIZE = _s["piles"]["section"]["size"]
BLOCK = _s["foundation"]["block"]
CHASSIS_H = _s["chassis"]["main_beams"]["depth"]
CELL = _s["chassis"]["cell_frame"]
CELL_H = CELL["depth"]
BRACING = _s["bracing"]["value"]
FLOOR_Z = PILE_H + CHASSIS_H + CELL_H     # viga I + bastidor de cajones
ROOF_Z = FLOOR_Z + HULL_H
SHELL_T, INS_T, LINING_T = (layer["thickness"] for layer in _e["layers_outside_in"])
STUD_STEP = _e["frame"]["stud"]["spacing"]
NOGGIN_STEP = _e["frame"]["noggin"]["spacing"]
PV_L, PV_W = SPEC["pv"]["panel"]["size"]
PV_T = SPEC["pv"]["panel"]["thickness"]["value"]
PV_ROWS, PV_COLS = SPEC["pv"]["array"]["rows"], SPEC["pv"]["array"]["cols"]
PV_GAP = 0.02
PV_FRAME_Z = ROOF_Z + SPEC["pv"]["frame"]["height_over_roof"]
TANK = tuple(SPEC["water"]["tank"]["size"])
PIT_X, PIT_Y = SPEC["water"]["tank"]["pit"]["center"]
PIT = tuple(SPEC["water"]["tank"]["pit"]["size"])
TERRACE_D = SPEC["terrace"]["depth"]
STAIR = SPEC["stair"]
NICHE = SPEC["tech_niche"]
_c = _e["cutaway"]
CUT_X0, CUT_X1 = _c["x_range"]
CUT_Z0, CUT_Z1 = FLOOR_Z + _c["z_from_floor"][0], ROOF_Z - 0.35
CUT_STEP = _c["step_beyond_lining"]

HERE = r"C:\Users\paolin\Desktop\DEPLOII\TINIHOUSE\blender"
TEX = os.path.join(HERE, "textures")
GLB_PATH = r"C:\Users\paolin\Desktop\DEPLOII\TINIHOUSE\public\models\tinyhouse.glb"

LAYERS = ["structure", "solar", "water", "envelope", "interior", "terrain"]
random.seed(7)

# ---------------------------------------------------------------- limpieza
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for blocks in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.images):
    for b in list(blocks):
        if b.users == 0:
            blocks.remove(b)

roots = {}
for name in LAYERS:
    empty = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(empty)
    roots[name] = empty

# ---------------------------------------------------------------- materiales
TILE = {}  # metros por repetición de textura, por material


def hexc(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb)


def _image(path, non_color=False):
    img = bpy.data.images.load(path, check_existing=True)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    return img


def mat(name, color="#ffffff", rough=0.6, metal=0.0, alpha=1.0, emit=None,
        tex=None, color_map=None, tile=1.0):
    """Material PBR. `tex` = id de ambientCG en blender/textures (rugosidad, normal y
    metalicidad si existe); `color_map` reemplaza el mapa de color."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hexc(color), 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except AttributeError:
            m.blend_method = "BLEND"
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*hexc(emit), 1)
        bsdf.inputs["Emission Strength"].default_value = 1.5
    TILE[name] = tile if (tex or color_map) else None
    if tex or color_map:
        base = os.path.join(TEX, tex, f"{tex}_1K-JPG") if tex else None
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = _image(color_map or f"{base}_Color.jpg")
        nt.links.new(n.outputs["Color"], bsdf.inputs["Base Color"])
        if base:
            for suffix, socket in (("Roughness", "Roughness"), ("Metalness", "Metallic")):
                p = f"{base}_{suffix}.jpg"
                if os.path.exists(p) and (socket != "Metallic" or metal > 0):
                    n = nt.nodes.new("ShaderNodeTexImage")
                    n.image = _image(p, True)
                    nt.links.new(n.outputs["Color"], bsdf.inputs[socket])
            p = f"{base}_NormalGL.jpg"
            if os.path.exists(p):
                n = nt.nodes.new("ShaderNodeTexImage")
                n.image = _image(p, True)
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nt.links.new(n.outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


GEN = os.path.join(TEX, "generated")
M = {
    "yellow": mat("hull_yellow", metal=0.3, tex="PaintedMetal006",
                  color_map=os.path.join(GEN, "hull_yellow_Color.jpg"), tile=2.4),
    "blue": mat("hull_blue", metal=0.3, tex="PaintedMetal006",
                color_map=os.path.join(GEN, "hull_blue_Color.jpg"), tile=2.4),
    "roof": mat("hull_roof", metal=0.3, tex="PaintedMetal013", tile=4.5),
    "stripe": mat("hull_stripe", "#1e293b", 0.5, 0.4),
    "glass": mat("glass", "#a5d8f0", 0.05, alpha=0.3),
    "steel": mat("steel_galv", metal=1.0, tex="Metal032", tile=1.0),
    "frame": mat("timber_frame", "#b0844f", 0.75),
    "dark": mat("steel_dark", "#334155", 0.5, 0.7),
    "concrete": mat("concrete", tex="Concrete034", tile=1.5),
    "deck": mat("wood_deck", tex="Planks037A", tile=1.6),
    "floor": mat("wood_floor", tex="WoodFloor051", tile=1.6),
    "oak": mat("wood_furniture", tex="WoodFloor051", tile=0.9),
    "lining": mat("lining_board", "#d9dcdf", 0.8),
    "plate": mat("steel_plate", "#a9b0b8", 0.55, 0.6),
    "wool": mat("mineral_wool", "#e9c84a", 1.0),
    "tiles": mat("tiles", rough=0.2, color_map=os.path.join(GEN, "tiles_Color.jpg"), tile=0.6),
    "pv": mat("pv_cell", rough=0.15, metal=0.2, color_map=os.path.join(GEN, "pv_cells_Color.jpg")),
    "pvframe": mat("pv_frame", "#c0c6cc", 0.3, 0.9),
    "cable": mat("cable", "#facc15", 0.5, emit="#facc15"),
    "grey_pipe": mat("pvc_grey", "#7dd3fc", 0.4, emit="#38bdf8"),
    "green_pipe": mat("pvc_treated", "#4ade80", 0.4, emit="#22c55e"),
    "water": mat("water", "#3b82f6", 0.05, alpha=0.55),
    "gravel": mat("gravel", tex="Gravel023", tile=0.8),
    "sand": mat("sand", tex="Ground054", tile=1.0),
    "topsoil": mat("topsoil", tex="Ground048", tile=0.8),
    "soil": mat("soil", tex="Ground048", tile=2.0),
    "grass": mat("grass", tex="Grass004", tile=2.0),
    "plant": mat("plant", "#4d7c0f", 0.8),
    "plant2": mat("plant_dry", "#8a8a3a", 0.9),
    "white": mat("ceramic", "#f1f5f9", 0.2),
    "cabinet": mat("cabinet_white", "#eef0f2", 0.45),
    "fabric": mat("fabric_grey", "#9aa3ae", 0.95),
    "linen": mat("fabric_linen", "#ece7de", 0.95),
    "rug": mat("rug", "#8c7b6b", 1.0),
    "black": mat("appliance_black", "#111827", 0.3, 0.2),
    "chrome": mat("chrome", "#e5e7eb", 0.1, 1.0),
    "screen": mat("screen", "#0f172a", 0.2, emit="#1e3a8a"),
    "led": mat("led_status", "#22c55e", 0.4, emit="#22c55e"),
    "lamp": mat("ceiling_lamp", "#fff7e6", 0.4, emit="#fff1d0"),
    "red": mat("tail_light", "#dc2626", 0.3, emit="#7f1d1d"),
    "books": [mat(f"book_{i}", c, 0.8) for i, c in enumerate(["#7c2d12", "#1e3a8a", "#065f46", "#a16207", "#475569"])],
}

# ---------------------------------------------------------------- utilidades


def _finish(ob, material, layer):
    if material is not None:
        ob.data.materials.append(material)
    ob.parent = roots[layer]
    return ob


def box(name, layer, size, loc, material, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 4
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return _finish(ob, material, layer)


def cyl(name, layer, r, depth, loc, material, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc,
                                        rotation=rot, vertices=verts)
    ob = bpy.context.active_object
    ob.name = name
    return _finish(ob, material, layer)


def pipe(name, layer, pts, material, r=0.03):
    """Tubería o perfil como curva con bisel, convertida a malla."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = (*co, 1)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return _finish(ob, material, layer)


def boolean(target, cutter, op="DIFFERENCE", self_overlap=False):
    mod = target.modifiers.new("bool", "BOOLEAN")
    mod.operation = op
    mod.object = cutter
    # el marco de perfiles son piezas unidas que se cruzan entre sí
    if self_overlap or "wall_frame" in target.name or "wall_frame" in cutter.name or "lining" in target.name:
        mod.use_self = True
        mod.use_hole_tolerant = True
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)


def split(target, cutter, piece_name):
    """Separa `target` en lo que queda fuera del cortador y la pieza retirada."""
    piece = target.copy()
    piece.data = target.data.copy()
    piece.name = piece_name
    bpy.context.scene.collection.objects.link(piece)
    boolean(piece, cutter, "INTERSECT")
    boolean(target, cutter, "DIFFERENCE")
    return piece


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


def assembly(name, layer, parts, loc, angle=0.0):
    """Une piezas modeladas en torno al origen y las ubica con un giro en Z."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob = join(parts, name)
    ob.location = loc
    ob.rotation_euler = (0, 0, angle)
    ob.parent = roots[layer]
    return ob


def rounded_shell(name, layer, size, center, thick, materials, bevel, assign=None):
    """Caja hueca redondeada (solidify hacia adentro). `assign(face_center, normal)`
    devuelve el índice de material de cada cara antes de engrosar."""
    ob = box(name, layer, size, center, None, bevel=bevel)
    for m in materials:
        ob.data.materials.append(m)
    if assign:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        z0 = center[2] - size[2] / 2
        # cortes horizontales para separar franjas de pintura
        for dz in (0.80, 0.95):
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z0 + dz), plane_no=(0, 0, 1))
        for f in bm.faces:
            f.material_index = assign(f.calc_center_median() + ob.location, f.normal)
        bm.to_mesh(ob.data)
        bm.free()
    mod = ob.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = thick
    mod.offset = -1
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return ob


def tuft(name, layer, loc, height=0.35, material=None):
    """Mata de pasto low-poly: hojas triangulares inclinadas."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for _ in range(7):
        a = random.uniform(0, 2 * math.pi)
        lean = random.uniform(0.1, 0.35)
        h = height * random.uniform(0.6, 1.1)
        d = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-d.y, d.x, 0)) * 0.025
        tip = d * lean * h + Vector((0, 0, h))
        bm.faces.new([bm.verts.new(-side), bm.verts.new(side), bm.verts.new(tip)])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    return _finish(ob, material or random.choice([M["plant"], M["plant"], M["plant2"]]), layer)


def column(prefix, x, y, top_z, size=PILE_SIZE, scale=1.0):
    """Pilar de perfil H con placa base sobre un dado de hormigón único."""
    (bx_, by_), (z0, z1) = BLOCK["size"], BLOCK["z"]
    box(f"{prefix}_block", "structure", (bx_ * scale, by_ * scale, z1 - z0), (x, y, (z0 + z1) / 2), M["concrete"])
    box(f"{prefix}_plate", "structure", (size + 0.1, size + 0.1, 0.02), (x, y, z1 + 0.01), M["steel"])
    h = top_z - z1 - 0.02
    zc = z1 + 0.02 + h / 2
    t = 0.012
    parts = [box(f"{prefix}_flange_a", "structure", (size, t, h), (x, y - size / 2 + t / 2, zc), M["steel"]),
             box(f"{prefix}_flange_b", "structure", (size, t, h), (x, y + size / 2 - t / 2, zc), M["steel"]),
             box(f"{prefix}_web", "structure", (0.008, size - 2 * t, h), (x, y, zc), M["steel"])]
    join(parts, prefix)


def i_beam(name, length, x_c, y, z_top, depth, flange, along="x"):
    """Viga I: dos alas y alma."""
    t = 0.014
    zc = z_top - depth / 2
    if along == "x":
        parts = [box(f"{name}_top", "structure", (length, flange, t), (x_c, y, z_top - t / 2), M["steel"]),
                 box(f"{name}_bot", "structure", (length, flange, t), (x_c, y, z_top - depth + t / 2), M["steel"]),
                 box(f"{name}_web", "structure", (length, 0.009, depth - 2 * t), (x_c, y, zc), M["steel"])]
    else:
        parts = [box(f"{name}_top", "structure", (flange, length, t), (x_c, y, z_top - t / 2), M["steel"]),
                 box(f"{name}_bot", "structure", (flange, length, t), (x_c, y, z_top - depth + t / 2), M["steel"]),
                 box(f"{name}_web", "structure", (0.009, length, depth - 2 * t), (x_c, y, zc), M["steel"])]
    return join(parts, name)


def x_brace(prefix, layer, a, b, y, z0, z1, r=0.02):
    pipe(f"{prefix}a", layer, [(a, y, z0), (b, y, z1)], M["steel"], r)
    pipe(f"{prefix}b", layer, [(a, y, z1), (b, y, z0)], M["steel"], r)


# ---------------------------------------------------------------- terreno
TER_L, TER_W, TER_D = 17.5, 9.0, 1.6
TER_CY = -0.8
soil = box("soil", "terrain", (TER_L, TER_W, TER_D), (0, TER_CY, -TER_D / 2), M["soil"])
grass = box("grass", "terrain", (TER_L, TER_W, 0.04), (0, TER_CY, 0.02), M["grass"])
pit_cutter = box("pit_cut", "terrain", (PIT[0], PIT[1], 2 * PIT[2]), (PIT_X, PIT_Y, 0), None)
boolean(soil, pit_cutter)
boolean(grass, pit_cutter)
bpy.data.objects.remove(pit_cutter, do_unlink=True)
pit_floor_z = -PIT[2]
box("pit_slab", "terrain", (PIT[0], PIT[1], 0.15), (PIT_X, PIT_Y, pit_floor_z + 0.075), M["concrete"])
for sx in (-1, 1):
    box(f"pit_wall_x{sx:+d}", "terrain", (0.1, PIT[1], PIT[2] + 0.15),
        (PIT_X + sx * (PIT[0] / 2 - 0.05), PIT_Y, pit_floor_z / 2 + 0.07), M["concrete"])
for sy in (-1, 1):
    box(f"pit_wall_y{sy:+d}", "terrain", (PIT[0], 0.1, PIT[2] + 0.15),
        (PIT_X, PIT_Y + sy * (PIT[1] / 2 - 0.05), pit_floor_z / 2 + 0.07), M["concrete"])
for k in range(100):
    x = random.uniform(-TER_L / 2 + 0.2, TER_L / 2 - 0.2)
    y = random.uniform(TER_CY - TER_W / 2 + 0.2, TER_CY + TER_W / 2 - 0.2)
    if abs(x - PIT_X) < PIT[0] / 2 + 0.2 and abs(y - PIT_Y) < PIT[1] / 2 + 0.2:
        continue
    tuft(f"tuft_{k:02d}", "terrain", (x, y, 0.04), random.uniform(0.2, 0.45))

# ---------------------------------------------------------------- estructura
# Pilares H sobre dados -> vigas I longitudinales -> bastidor de cajones de plancha
# de acero que recibe el piso del casco y el de la terraza (todo un mismo sistema).
CH_X0 = -HULL_L / 2
CH_X1 = HULL_L / 2 + TERRACE_D
beam_top = PILE_H + CHASSIS_H
_mb = _s["chassis"]["main_beams"]
for i, x in enumerate(PILE_XS):
    for j, y in enumerate(PILE_YS):
        column(f"pile_{i}{j}", x, y, PILE_H)
end_x = CH_X1 - 0.1  # pilares de la terraza
for j, y in enumerate(PILE_YS):
    column(f"terrace_post_{j}", end_x, y, PILE_H, size=_s["terrace_posts"]["section"], scale=0.8)
for j, y in enumerate(PILE_YS):
    i_beam(f"main_beam_{j}", CH_X1 - CH_X0, (CH_X0 + CH_X1) / 2, y, beam_top, CHASSIS_H, _mb["flange"])
for i, x in enumerate(PILE_XS + [end_x]):  # cabezales transversales sobre cada línea de pilares
    i_beam(f"cross_beam_{i}", 2.35, x, 0, beam_top, CHASSIS_H * 0.8, 0.1, along="y")

# bastidor de cajones: plancha inferior, planchas longitudinales y tabiques cada 1,2 m
pt = CELL["plate"]
cz0, cz1 = beam_top, FLOOR_Z
czc = (cz0 + cz1) / 2
cell_w = HULL_W - 0.1
box("cells_bottom", "structure", (CH_X1 - CH_X0, cell_w, pt), ((CH_X0 + CH_X1) / 2, 0, cz0 + pt / 2), M["plate"])
for y in CELL["longitudinal_plates_y"]:
    box(f"cells_long_{y:+.1f}", "structure", (CH_X1 - CH_X0, pt, CELL_H), ((CH_X0 + CH_X1) / 2, y, czc), M["plate"])
front_plate = box("cutaway_chassis_front", "structure", (CH_X1 - CH_X0, pt, CELL_H),
                  ((CH_X0 + CH_X1) / 2, -cell_w / 2, czc), M["plate"])
n_cells = round((CH_X1 - CH_X0) / CELL["cell_length"])
for k in range(n_cells + 1):
    x = CH_X0 + k * (CH_X1 - CH_X0) / n_cells
    box(f"cells_cross_{k:02d}", "structure", (pt, cell_w, CELL_H), (x, 0, czc), M["plate"])
box("cells_top_rim", "structure", (CH_X1 - CH_X0, cell_w, 0.012), ((CH_X0 + CH_X1) / 2, 0, cz1 - 0.006), M["steel"])
if BRACING:
    for j, y in enumerate(PILE_YS):
        for i, (a, b) in enumerate(zip(PILE_XS + [end_x], (PILE_XS + [end_x])[1:])):
            x_brace(f"brace_{j}{i}", "structure", a, b, y, 0.45, PILE_H - 0.05)

# terraza (+X): entablado sobre el bastidor de cajones, a nivel del piso interior
tx0, tx1 = HULL_L / 2, CH_X1
tw = HULL_W
for k in range(int(TERRACE_D / 0.15)):
    box(f"terrace_board_{k:02d}", "structure", (0.135, tw, 0.03), (tx0 + 0.075 + k * 0.15, 0, FLOOR_Z + 0.015), M["deck"])
RAIL_H = 1.0
deck_z = FLOOR_Z + 0.03


def railing(prefix, pts, top=RAIL_H, base=None):
    base = deck_z if base is None else base
    for h, r in ((top, 0.025), (top * 0.55, 0.015), (0.12, 0.015)):
        pipe(f"{prefix}_rail_{h:.2f}", "structure", [(x, y, base + h) for x, y in pts], M["steel"], r)
    for a, b in zip(pts, pts[1:]):
        seg = Vector((b[0] - a[0], b[1] - a[1], 0))
        n = max(1, round(seg.length / 0.6))
        for k in range(n + 1):
            p = Vector((a[0], a[1], 0)) + seg * (k / n)
            box(f"{prefix}_post_{p.x:.2f}_{p.y:.2f}", "structure", (0.04, 0.04, top), (p.x, p.y, base + top / 2), M["steel"])


railing("terrace", [(tx0 + 0.05, -tw / 2 + 0.04), (tx1 - 0.04, -tw / 2 + 0.04),
                    (tx1 - 0.04, tw / 2 - 0.04), (tx0 + 0.05, tw / 2 - 0.04)])

# acceso lateral: antigua puerta de pasajeros en el costado +Y, cerca del extremo
# trasero; descanso en ménsula y escalera paralela al costado bajando hacia -X
DOOR_X = STAIR["door"]["x_center"]
LW, LD = STAIR["landing"]["size"]
STAIR_W = STAIR["width"]
ly0 = HULL_W / 2 + 0.02
lyc = ly0 + LD / 2
lx0, lx1 = DOOR_X - LW / 2, DOOR_X + LW / 2
for k in range(int(LW / 0.15)):
    box(f"landing_board_{k}", "structure", (0.135, LD, 0.03), (lx0 + 0.075 + k * 0.15, lyc, FLOOR_Z + 0.015), M["deck"])
for x in (lx0 + 0.05, lx1 - 0.05):  # ménsulas desde el bastidor de cajones
    box(f"landing_bracket_{x:+.2f}", "structure", (0.06, LD + 0.1, 0.12), (x, lyc - 0.05, FLOOR_Z - 0.06), M["steel"])
    pipe(f"landing_strut_{x:+.2f}", "structure", [(x, ly0 - 0.02, FLOOR_Z - 0.4), (x, ly0 + LD - 0.05, FLOOR_Z - 0.1)], M["steel"], 0.025)
column("landing_post", lx1 - 0.06, ly0 + LD - 0.08, FLOOR_Z - 0.12, size=0.1, scale=0.6)
railing("landing", [(lx0 + 0.03, ly0 + LD - 0.03), (lx1 - 0.03, ly0 + LD - 0.03), (lx1 - 0.03, ly0 + 0.03)])
n_steps = STAIR["steps"]
rise = deck_z / n_steps
run = STAIR["run"]
stair_y = ly0 + STAIR_W / 2
sx_top = lx0
sx_bot = sx_top - (n_steps - 1) * run
box("stair_pad", "structure", (0.5, STAIR_W + 0.3, 0.2), (sx_bot - 0.15, stair_y, 0.05), M["concrete"])
for st_ in range(1, n_steps):
    box(f"stair_tread_{st_}", "structure", (run + 0.02, STAIR_W, 0.035),
        (sx_top - (st_ - 0.5) * run, stair_y, deck_z - st_ * rise), M["deck"])
for dy in (-STAIR_W / 2, STAIR_W / 2):
    y = stair_y + dy
    a = Vector((sx_top, y, FLOOR_Z - 0.08))
    b = Vector((sx_bot - 0.1, y, 0.12))
    d = b - a
    box(f"stringer_{dy:+.1f}", "structure", (d.length, 0.05, 0.2), (a + b) / 2, M["steel"],
        rot=(0, -math.atan2(-d.z, -d.x), 0))
y_out = stair_y + STAIR_W / 2
pipe("handrail", "structure", [(sx_top, y_out, deck_z + 0.95), (sx_bot, y_out, 0.15 + 0.9), (sx_bot, y_out, 0.15)], M["steel"], 0.02)

# ---------------------------------------------------------------- envolvente
hull_c = (0, 0, FLOOR_Z + HULL_H / 2)


def paint(c, n):
    if n.z > 0.6 and c.z > ROOF_Z - 0.4:
        return 2  # cubierta
    if n.z < -0.6 or c.z < FLOOR_Z + 0.80:
        return 1  # zócalo azul
    if c.z < FLOOR_Z + 0.95:
        return 3  # franja oscura
    return 0      # amarillo


hull = rounded_shell("hull", "envelope", (HULL_L, HULL_W, HULL_H), hull_c, SHELL_T,
                     [M["yellow"], M["blue"], M["roof"], M["stripe"]], HULL_R, paint)
in1 = (HULL_L - 2 * SHELL_T, HULL_W - 2 * SHELL_T, HULL_H - 2 * SHELL_T)
ins = rounded_shell("insulation", "envelope", in1, hull_c, INS_T, [M["wool"]], HULL_R - SHELL_T)
in2 = tuple(d - 2 * INS_T for d in in1)
lining = rounded_shell("lining", "envelope", in2, hull_c, LINING_T, [M["lining"]], HULL_R - SHELL_T - INS_T)

# perfiles de acero galvanizado dentro de la capa de aislación: montantes,
# soleras, cerchas de cubierta y vigas de piso cada 0,6 m
frame_parts = []
y_stud = HULL_W / 2 - SHELL_T - INS_T / 2
FRAME_T = INS_T + 0.004  # algo más que la lana, para un corte booleano limpio
z_lo, z_hi = FLOOR_Z + HULL_R, ROOF_Z - HULL_R
flat_w = HULL_W - 2 * HULL_R
x = -HULL_L / 2 + HULL_R
while x <= HULL_L / 2 - HULL_R + 1e-6:
    for side in (-1, 1):
        frame_parts.append(box(f"stud_{x:+.2f}_{side:+d}", "envelope", (0.05, FRAME_T, z_hi - z_lo),
                               (x, side * y_stud, (z_lo + z_hi) / 2), M["frame"]))
    frame_parts.append(box(f"rafter_{x:+.2f}", "envelope", (0.05, flat_w, FRAME_T),
                           (x, 0, ROOF_Z - SHELL_T - INS_T / 2), M["frame"]))
    frame_parts.append(box(f"floor_joist_{x:+.2f}", "envelope", (0.05, flat_w, FRAME_T),
                           (x, 0, FLOOR_Z + SHELL_T + INS_T / 2), M["frame"]))
    x += STUD_STEP
# travesaños horizontales: la lana queda en placas de STUD_STEP x NOGGIN_STEP
n_nog = int((z_hi - z_lo) / NOGGIN_STEP)
nog_zs = [z_lo + k * (z_hi - z_lo) / n_nog for k in range(n_nog + 1)]
for side in (-1, 1):
    for z in nog_zs:
        frame_parts.append(box(f"plate_{side:+d}_{z:.2f}", "envelope", (HULL_L - 2 * HULL_R, FRAME_T, 0.05),
                               (0, side * y_stud, z), M["frame"]))
frame = join(frame_parts, "wall_frame")
boolean(ins, frame)  # la lana queda entre perfiles

# vanos permanentes: ventanas y puertas
win_z, win_h = FLOOR_Z + 1.75, 0.85
door_h = 1.95
cutters = []
n_win = 6
for k in range(n_win):  # muro posterior (+Y)
    x = -HULL_L / 2 + 1.2 + k * (HULL_L - 2.4) / (n_win - 1)
    if abs(x - DOOR_X) < 1.0:
        continue  # aquí va la puerta de pasajeros
    cutters.append(box(f"c_win{k}", "envelope", (1.1, 0.8, win_h), (x, HULL_W / 2, win_z), None))
    box(f"window_{k}", "envelope", (1.1, 0.02, win_h), (x, HULL_W / 2 - 0.06, win_z), M["glass"])
_dw, _dh = STAIR["door"]["width"], STAIR["door"]["height"]
cutters.append(box("c_side_door", "envelope", (_dw, 0.8, _dh), (DOOR_X, HULL_W / 2, FLOOR_Z + 0.08 + _dh / 2), None))
for k, dx in enumerate((-_dw / 4, _dw / 4)):  # puerta plegable de bus, dos hojas vidriadas
    box(f"side_door_leaf_{k}", "envelope", (_dw / 2 - 0.02, 0.03, _dh - 0.02), (DOOR_X + dx, HULL_W / 2 - 0.03, FLOOR_Z + 0.08 + _dh / 2), M["yellow"])
    box(f"side_door_glass_{k}", "envelope", (_dw / 2 - 0.12, 0.035, _dh * 0.7), (DOOR_X + dx, HULL_W / 2 - 0.03, FLOOR_Z + 0.08 + _dh * 0.55), M["glass"])
cutters.append(box("c_rear_door", "envelope", (0.8, 0.85, door_h), (-HULL_L / 2, 0, FLOOR_Z + 0.12 + door_h / 2), None))
box("rear_door", "envelope", (0.03, 0.82, door_h - 0.02), (-HULL_L / 2 + 0.03, 0, FLOOR_Z + 0.12 + door_h / 2), M["yellow"])
for k, zc in enumerate((FLOOR_Z + 1.55, FLOOR_Z + 0.75)):
    box(f"rear_door_glass_{k}", "envelope", (0.035, 0.6, 0.6), (-HULL_L / 2 + 0.03, 0, zc), M["glass"])
for y in (-0.8, 0.8):
    cutters.append(box(f"c_rear_win{y:+.1f}", "envelope", (0.8, 0.5, 0.9), (-HULL_L / 2, y, win_z), None))
    box(f"rear_window_{y:+.1f}", "envelope", (0.02, 0.5, 0.9), (-HULL_L / 2 + 0.12, y, win_z), M["glass"])
    box(f"tail_light_{y:+.1f}", "envelope", (0.05, 0.16, 0.16), (-HULL_L / 2 - 0.01, y * 1.25, FLOOR_Z + 0.55), M["red"])
    box(f"tail_light_top_{y:+.1f}", "envelope", (0.05, 0.12, 0.12), (-HULL_L / 2 + 0.05, y * 1.1, ROOF_Z - 0.3), M["red"])
cutters.append(box("c_terrace_door", "envelope", (0.8, 0.85, door_h), (HULL_L / 2, 0.45, FLOOR_Z + 0.12 + door_h / 2), None))
box("terrace_door", "envelope", (0.03, 0.82, door_h - 0.02), (HULL_L / 2 - 0.03, 0.45, FLOOR_Z + 0.12 + door_h / 2), M["blue"])
box("terrace_door_glass", "envelope", (0.035, 0.55, 0.9), (HULL_L / 2 - 0.03, 0.45, FLOOR_Z + 1.4), M["glass"])
cutters.append(box("c_terrace_win", "envelope", (0.8, 0.8, 0.9), (HULL_L / 2, -0.6, win_z), None))
box("terrace_window", "envelope", (0.02, 0.8, 0.9), (HULL_L / 2 - 0.12, -0.6, win_z), M["glass"])
cutter = join(cutters, "cutters")
for target in (hull, ins, lining, frame):
    boolean(target, cutter)
bpy.data.objects.remove(cutter, do_unlink=True)

# corte frontal escalonado: cada capa exterior se retira un poco más que la
# interior, dejando a la vista chapa, perfiles con lana y revestimiento
for target in (hull, ins, frame, lining):
    e = CUT_STEP[target.name]
    c = box(f"c_cut_{target.name}", "envelope", (CUT_X1 - CUT_X0 + 2 * e, 0.8, CUT_Z1 - CUT_Z0 + 2 * e),
            ((CUT_X0 + CUT_X1) / 2, -HULL_W / 2, (CUT_Z0 + CUT_Z1) / 2), None)
    split(target, c, f"cutaway_{target.name}")
    bpy.data.objects.remove(c, do_unlink=True)

for y in (-0.85, 0.85):
    cyl(f"headlamp_{y:+.1f}", "envelope", 0.1, 0.05, (HULL_L / 2 + 0.01, y, FLOOR_Z + 0.55), M["white"], rot=(0, math.pi / 2, 0))
for y in (-1, 1):  # espejos de bus en el extremo de la terraza
    pipe(f"mirror_arm_{y:+d}", "envelope", [(HULL_L / 2 - 0.15, y * (HULL_W / 2), ROOF_Z - 0.4),
                                             (HULL_L / 2 + 0.15, y * (HULL_W / 2 + 0.25), ROOF_Z - 0.4)], M["dark"], 0.015)
    box(f"mirror_{y:+d}", "envelope", (0.04, 0.18, 0.32), (HULL_L / 2 + 0.17, y * (HULL_W / 2 + 0.27), ROOF_Z - 0.55), M["dark"], bevel=0.015)
_sk = SPEC["pv"]["skylight"]
box("skylight_frame", "envelope", (_sk["size"][0] + 0.08, _sk["size"][1] + 0.08, 0.1), (_sk["x"], 0, ROOF_Z + 0.03), M["dark"])
box("skylight", "envelope", (_sk["size"][0], _sk["size"][1], 0.03), (_sk["x"], 0, ROOF_Z + 0.09), M["glass"])
for sx in (-1, 1):
    box(f"bumper_{sx:+d}", "envelope", (0.1, HULL_W - 0.2, 0.18), (sx * (HULL_L / 2 + 0.02), 0, FLOOR_Z + 0.3), M["dark"])

# ---------------------------------------------------------------- interior
fz = FLOOR_Z + SHELL_T + INS_T + LINING_T
box("floor_boards", "interior", (HULL_L - 0.9, HULL_W - 0.3, 0.025), (0, 0, fz + 0.0125), M["floor"])
fz += 0.025
iy = HULL_W / 2 - SHELL_T - INS_T - LINING_T  # semiancho interior
ceil_z = ROOF_Z - SHELL_T - INS_T - LINING_T
wall_h = ceil_z - fz - 0.15
# tabiques: dormitorio | closet técnico | baño | hall de la terraza
CORRIDOR_Y = -0.35  # borde frontal de los tabiques del nicho
WALLS = {"wall_bed": -2.4, "wall_tech": 1.0, "wall_bath_w": 1.6, "wall_bath_e": 3.6}
for name, x in WALLS.items():
    if name == "wall_bed":  # tabique bajo con paso, separa cocina y dormitorio
        box(name, "interior", (0.06, iy, wall_h), (x, iy / 2, fz + wall_h / 2), M["lining"])
    elif name in ("wall_tech", "wall_bath_w"):  # dejan un pasillo frente al nicho técnico
        box(name, "interior", (0.06, iy - CORRIDOR_Y, wall_h), (x, (iy + CORRIDOR_Y) / 2, fz + wall_h / 2), M["lining"])
    else:
        box(name, "interior", (0.06, 2 * iy - 0.05, wall_h), (x, 0, fz + wall_h / 2), M["lining"])
for k, x in enumerate((-3.6, -1.2, 1.3, 2.6, 4.3)):
    cyl(f"ceiling_lamp_{k}", "interior", 0.13, 0.03, (x, 0, ceil_z - 0.02), M["lamp"])


def chair(name, loc, angle):
    parts = [box(f"{name}_seat", "interior", (0.42, 0.42, 0.04), (0, 0, 0.45), M["oak"]),
             box(f"{name}_back", "interior", (0.42, 0.03, 0.4), (0, 0.2, 0.7), M["oak"])]
    for lx in (-0.18, 0.18):
        for ly in (-0.18, 0.18):
            parts.append(cyl(f"{name}_leg", "interior", 0.015, 0.45, (lx, ly, 0.225), M["dark"], verts=8))
    return assembly(name, "interior", parts, loc, angle)


def books(prefix, x0, x1, y, z, depth=0.2):
    x = x0
    k = 0
    while x < x1:
        w = random.uniform(0.025, 0.05)
        h = random.uniform(0.18, 0.28)
        box(f"{prefix}_{k}", "interior", (w, depth, h), (x + w / 2, y, z + h / 2), random.choice(M["books"]))
        x += w + 0.004
        k += 1


# cocina y comedor (-X), junto a la puerta trasera
kx0, kx1 = DOOR_X + _dw / 2 + 0.15, -2.95
ky = iy - 0.3
box("kitchen_base", "interior", (kx1 - kx0, 0.6, 0.86), ((kx0 + kx1) / 2, ky, fz + 0.43), M["cabinet"])
for k in range(3):
    box(f"kitchen_door_{k}", "interior", ((kx1 - kx0) / 3 - 0.01, 0.01, 0.7),
        (kx0 + (k + 0.5) * (kx1 - kx0) / 3, ky - 0.305, fz + 0.45), M["cabinet"])
box("kitchen_top", "interior", (kx1 - kx0 + 0.02, 0.62, 0.035), ((kx0 + kx1) / 2, ky, fz + 0.88), M["oak"])
box("kitchen_sink", "interior", (0.45, 0.38, 0.02), (kx0 + 0.4, ky, fz + 0.9), M["chrome"])
cyl("kitchen_tap", "interior", 0.015, 0.3, (kx0 + 0.4, ky + 0.22, fz + 1.05), M["chrome"], verts=8)
box("cooktop", "interior", (0.5, 0.45, 0.01), (kx1 - 0.35, ky, fz + 0.9), M["black"])
for dx in (-0.12, 0.12):
    cyl(f"burner_{dx:+.2f}", "interior", 0.07, 0.006, (kx1 - 0.35 + dx, ky, fz + 0.906), M["dark"])
box("upper_cabinets", "interior", (kx1 - kx0, 0.35, 0.6), ((kx0 + kx1) / 2, iy - 0.18, fz + 1.75), M["cabinet"])
box("range_hood", "interior", (0.5, 0.4, 0.12), (kx1 - 0.35, iy - 0.2, fz + 1.4), M["chrome"])
box("fridge", "interior", (0.6, 0.62, 1.75), (-2.68 - 0.02, iy - 0.32, fz + 0.875), M["chrome"], bevel=0.02)
box("table", "interior", (0.8, 0.7, 0.035), (-3.55, -0.5, fz + 0.74), M["oak"])
cyl("table_leg", "interior", 0.04, 0.72, (-3.55, -0.5, fz + 0.36), M["dark"])
chair("chair_a", (-4.1, -0.5, fz), math.pi / 2)
chair("chair_b", (-3.0, -0.5, fz), -math.pi / 2)
cyl("fruit_bowl", "interior", 0.12, 0.06, (-3.55, -0.5, fz + 0.79), M["white"])

# dormitorio con escritorio
bx, by = -1.3, iy - 0.74
box("bed_base", "interior", (2.0, 1.45, 0.32), (bx, by, fz + 0.16), M["oak"])
for dx in (-0.5, 0.5):
    box(f"bed_drawer_{dx:+.1f}", "interior", (0.9, 0.01, 0.22), (bx + dx, by - 0.73, fz + 0.16), M["cabinet"])
box("mattress", "interior", (1.95, 1.4, 0.2), (bx, by, fz + 0.42), M["linen"], bevel=0.03)
box("duvet", "interior", (1.4, 1.46, 0.07), (bx + 0.3, by, fz + 0.55), M["fabric"], bevel=0.03)
for dy in (-0.33, 0.33):
    box(f"pillow_{dy:+.2f}", "interior", (0.32, 0.6, 0.13), (bx - 0.78, by + dy, fz + 0.6), M["linen"], bevel=0.05)
box("headboard", "interior", (0.08, 1.45, 0.75), (bx - 1.02, by, fz + 0.62), M["fabric"], bevel=0.02)
for k in range(2):
    sz = fz + 1.35 + k * 0.38
    box(f"bed_shelf_{k}", "interior", (1.4, 0.24, 0.025), (bx, iy - 0.12, sz), M["oak"])
    books(f"bed_books_{k}", bx - 0.65, bx - 0.05 + k * 0.3, iy - 0.13, sz + 0.0125)
box("storage_box", "interior", (0.3, 0.22, 0.2), (bx + 0.45, iy - 0.13, fz + 1.475), M["linen"])
box("rug", "interior", (1.6, 0.9, 0.01), (bx + 0.2, -0.5, fz + 0.005), M["rug"])
dx0 = 0.0
box("desk_top", "interior", (0.95, 0.5, 0.035), (dx0 + 0.47, iy - 0.25, fz + 0.74), M["oak"])
for lx in (dx0 + 0.04, dx0 + 0.9):
    box(f"desk_leg_{lx:.2f}", "interior", (0.04, 0.46, 0.72), (lx, iy - 0.25, fz + 0.36), M["oak"])
box("laptop_base", "interior", (0.32, 0.22, 0.015), (dx0 + 0.4, iy - 0.3, fz + 0.765), M["dark"])
box("laptop_screen", "interior", (0.32, 0.015, 0.21), (dx0 + 0.4, iy - 0.19, fz + 0.87), M["screen"], rot=(math.radians(-12), 0, 0))
cyl("desk_lamp_base", "interior", 0.06, 0.02, (dx0 + 0.8, iy - 0.15, fz + 0.77), M["dark"])
pipe("desk_lamp_arm", "interior", [(dx0 + 0.8, iy - 0.15, fz + 0.77), (dx0 + 0.78, iy - 0.18, fz + 1.1), (dx0 + 0.68, iy - 0.25, fz + 1.12)], M["dark"], 0.008)
cyl("desk_lamp_head", "interior", 0.05, 0.06, (dx0 + 0.66, iy - 0.25, fz + 1.09), M["lamp"])
chair("desk_chair", (dx0 + 0.45, iy - 0.8, fz), math.pi)
box("desk_shelf", "interior", (0.95, 0.22, 0.025), (dx0 + 0.47, iy - 0.11, fz + 1.4), M["oak"])
books("desk_books", dx0 + 0.05, dx0 + 0.45, iy - 0.12, fz + 1.4125)
cyl("plant_pot", "interior", 0.13, 0.28, (-0.2, -iy + 0.25, fz + 0.14), M["white"])
for k in range(5):
    tuft(f"pot_plant_{k}", "interior", (-0.2 + random.uniform(-0.05, 0.05), -iy + 0.25 + random.uniform(-0.05, 0.05), fz + 0.28), 0.45, M["plant"])

# nicho técnico entre dormitorio y baño: panel de fondo paralelo al frente; los
# equipos (capa solar, más abajo) se montan en su cara frontal, mirando al corte
nx0, nx1 = NICHE["location"]["x_range"]
niche_y = NICHE["back_panel"]["y"]
box("niche_back", "interior", (nx1 - nx0 - 0.06, 0.04, wall_h), ((nx0 + nx1) / 2, niche_y + 0.02, fz + wall_h / 2), M["lining"])

# baño
bath_x0, bath_x1 = WALLS["wall_bath_w"] + 0.03, WALLS["wall_bath_e"] - 0.03
tile_h = wall_h
box("tiles_back", "interior", (bath_x1 - bath_x0, 0.01, tile_h), ((bath_x0 + bath_x1) / 2, iy - 0.005, fz + tile_h / 2), M["tiles"])
box("tiles_w", "interior", (0.01, iy - CORRIDOR_Y, tile_h), (bath_x0 + 0.005, (iy + CORRIDOR_Y) / 2, fz + tile_h / 2), M["tiles"])
box("tiles_e", "interior", (0.01, 2 * iy - 0.05, tile_h), (bath_x1 - 0.005, 0, fz + tile_h / 2), M["tiles"])
box("tiles_floor", "interior", (bath_x1 - bath_x0, 2 * iy - 0.05, 0.01), ((bath_x0 + bath_x1) / 2, 0, fz + 0.005), M["tiles"])
sh_x0, sh_y0 = bath_x1 - 0.85, 0.05
sh_cx, sh_cy = (sh_x0 + bath_x1) / 2, (sh_y0 + iy) / 2
box("shower_tray", "interior", (bath_x1 - sh_x0, iy - sh_y0, 0.05), (sh_cx, sh_cy, fz + 0.035), M["white"])
box("shower_glass_x", "interior", (0.012, iy - sh_y0, 2.0), (sh_x0, sh_cy, fz + 1.06), M["glass"])
box("shower_glass_y", "interior", (bath_x1 - sh_x0, 0.012, 2.0), (sh_cx, sh_y0, fz + 1.06), M["glass"])
pipe("shower_riser", "interior", [(sh_cx, iy - 0.03, fz + 0.9), (sh_cx, iy - 0.03, fz + 2.15), (sh_cx, iy - 0.3, fz + 2.15)], M["chrome"], 0.012)
cyl("shower_rain_head", "interior", 0.12, 0.015, (sh_cx, iy - 0.3, fz + 2.13), M["chrome"])
box("shower_mixer", "interior", (0.12, 0.05, 0.08), (sh_cx, iy - 0.03, fz + 1.1), M["chrome"])
tx = 2.4  # inodoro
cyl("toilet_bowl", "interior", 0.19, 0.38, (tx, iy - 0.38, fz + 0.19), M["white"], verts=32)
box("toilet_seat", "interior", (0.38, 0.45, 0.03), (tx, iy - 0.36, fz + 0.4), M["white"], bevel=0.012)
box("toilet_tank", "interior", (0.38, 0.17, 0.4), (tx, iy - 0.09, fz + 0.6), M["white"], bevel=0.03)
skx = 1.95  # lavamanos con mueble
box("vanity", "interior", (0.5, 0.4, 0.45), (skx, iy - 0.21, fz + 0.6), M["oak"])
box("basin", "interior", (0.48, 0.38, 0.1), (skx, iy - 0.21, fz + 0.88), M["white"], bevel=0.04)
cyl("basin_tap", "interior", 0.012, 0.18, (skx, iy - 0.06, fz + 1.0), M["chrome"], verts=8)
box("mirror", "interior", (0.45, 0.01, 0.6), (skx, iy - 0.015, fz + 1.45), M["glass"])
box("bath_shelf", "interior", (0.4, 0.12, 0.02), (skx, iy - 0.07, fz + 1.12), M["white"])
pipe("towel_rail", "interior", [(bath_x0 + 0.03, -0.2, fz + 1.2), (bath_x0 + 0.08, -0.2, fz + 1.2),
                                (bath_x0 + 0.08, -0.75, fz + 1.2), (bath_x0 + 0.03, -0.75, fz + 1.2)], M["chrome"], 0.01)
box("towel", "interior", (0.02, 0.5, 0.45), (bath_x0 + 0.08, -0.47, fz + 1.0), M["linen"])

# hall de la terraza
box("shoe_bench", "interior", (0.9, 0.35, 0.45), (4.3, -iy + 0.2, fz + 0.225), M["oak"])
box("bench_cushion", "interior", (0.88, 0.33, 0.05), (4.3, -iy + 0.2, fz + 0.475), M["fabric"])
for k in range(3):
    cyl(f"coat_hook_{k}", "interior", 0.012, 0.08, (4.0 + k * 0.3, iy - 0.04, fz + 1.7), M["chrome"], rot=(math.pi / 2, 0, 0), verts=8)

# ---------------------------------------------------------------- solar
arr_len = PV_COLS * (PV_W + PV_GAP)
arr_w = PV_ROWS * (PV_L + PV_GAP)
post_xs = [-arr_len / 2 + 0.1, -arr_len / 6, arr_len / 6, arr_len / 2 - 0.1]
post_y = arr_w / 2 - 0.05
for x in post_xs:
    for y in (-post_y, post_y):
        box(f"pv_post_{x:+.1f}_{y:+.1f}", "solar", (0.06, 0.06, PV_FRAME_Z - ROOF_Z + 0.2),
            (x, y, (PV_FRAME_Z + ROOF_Z - 0.2) / 2), M["steel"])
    box(f"pv_cross_{x:+.1f}", "solar", (0.06, arr_w, 0.08), (x, 0, PV_FRAME_Z), M["steel"])
for y in (-post_y, 0, post_y):
    box(f"pv_rail_{y:+.1f}", "solar", (arr_len + 0.1, 0.06, 0.08), (0, y, PV_FRAME_Z), M["steel"])
for y in (-post_y, post_y):
    for x0, x1 in zip(post_xs, post_xs[1:]):
        x_brace(f"pv_brace_{x0:+.1f}_{y:+.1f}", "solar", x0, x1, y, ROOF_Z - 0.1, PV_FRAME_Z - 0.04, 0.015)
pz = PV_FRAME_Z + 0.04 + PV_T / 2
for r in range(PV_ROWS):
    y = -arr_w / 2 + (r + 0.5) * (PV_L + PV_GAP)
    for c in range(PV_COLS):
        x = -arr_len / 2 + (c + 0.5) * (PV_W + PV_GAP)
        box(f"pv_{r}{c}", "solar", (PV_W - 0.02, PV_L - 0.02, PV_T), (x, y, pz), M["pv"])
        box(f"pv_frame_{r}{c}", "solar", (PV_W, PV_L, PV_T * 0.8), (x, y, pz - 0.004), M["pvframe"])
# nicho técnico: inversor, tablero, datalogger y batería sobre el panel de fondo
ncx = (nx0 + nx1) / 2
face = niche_y  # cara frontal del panel


def niche_box(name, key, material, bevel=0.0):
    w, d, h = NICHE[key]["size"]
    c = (ncx, face - d / 2, fz + NICHE[key]["center_z_from_floor"])
    box(name, "solar", (w, d, h), c, material, bevel=bevel)
    return c, (w, d, h)


inv, (iw, idp, ih) = niche_box("inverter", "inverter", M["white"], 0.02)
box("inverter_display", "solar", (0.16, 0.01, 0.08), (inv[0], inv[1] - idp / 2 - 0.005, inv[2] + 0.1), M["screen"])
box("inverter_led", "solar", (0.03, 0.01, 0.015), (inv[0] + 0.13, inv[1] - idp / 2 - 0.005, inv[2] + 0.1), M["led"])
pan, (pw, pd, ph) = niche_box("electrical_panel", "electrical_panel", M["cabinet"])
box("electrical_panel_door", "solar", (pw - 0.04, 0.01, ph - 0.04), (pan[0], pan[1] - pd / 2 - 0.005, pan[2]), M["chrome"])
log, (lw, ld, lh) = niche_box("datalogger", "datalogger", M["dark"])
box("datalogger_led", "solar", (0.03, 0.005, 0.015), (log[0] + 0.05, log[1] - ld / 2 - 0.003, log[2] + 0.03), M["led"])
bat, (bw, bd, bh) = niche_box("battery", "battery", M["dark"], 0.015)
for k in range(5):  # rejilla de ventilación
    box(f"battery_grille_{k}", "solar", (bw - 0.1, 0.01, 0.015), (bat[0], bat[1] - bd / 2 - 0.005, bat[2] + 0.12 - k * 0.05), M["steel"])
cable_x = post_xs[2]
cy = face - 0.02  # canalización por la cara del panel
pipe("pv_cable", "solar",
     [(cable_x, -post_y, PV_FRAME_Z), (cable_x, -post_y, ROOF_Z - 0.05), (ncx - 0.15, cy, ROOF_Z - 0.05),
      (ncx - 0.15, cy, pan[2] + ph / 2)], M["cable"], 0.018)
pipe("pv_to_inverter", "solar", [(ncx - 0.15, cy, pan[2] - ph / 2), (ncx - 0.15, cy, inv[2] + ih / 2)], M["cable"], 0.018)
pipe("dc_cable", "solar", [(ncx + 0.15, cy, inv[2] - ih / 2), (ncx + 0.15, cy, bat[2] + bh / 2)], M["cable"], 0.018)
pipe("grid_cable", "solar", [(ncx - 0.2, cy, bat[2]), (ncx - 0.2, cy, 1.2), (0.0, -1.0, 1.2), (0.0, -1.0, 0.9)], M["cable"], 0.018)
box("meter_box", "solar", (0.25, 0.12, 0.3), (0.0, -1.0, 0.75), M["white"])

# ---------------------------------------------------------------- agua
tz = pit_floor_z + 0.15
tank_x = PIT_X - 0.3
box("tank", "water", TANK, (tank_x, PIT_Y, tz + TANK[2] / 2), M["glass"])
box("tank_water", "water", (TANK[0] - 0.04, TANK[1] - 0.04, TANK[2] * 0.7),
    (tank_x, PIT_Y, tz + TANK[2] * 0.35 + 0.02), M["water"])
pump_x = tank_x + TANK[0] / 2 + 0.3
cyl("pump", "water", 0.14, 0.32, (pump_x, PIT_Y, tz + 0.2), M["dark"], rot=(0, math.pi / 2, 0))
cyl("pump_motor", "water", 0.1, 0.2, (pump_x + 0.25, PIT_Y, tz + 0.2), M["steel"], rot=(0, math.pi / 2, 0))
bf_x, bf_y, bf_size = -1.2, -0.3, (1.6, 1.2)
bf_h = 0.7
for sx in (-1, 1):
    box(f"bio_wall_x{sx:+d}", "water", (0.06, bf_size[1], bf_h), (bf_x + sx * bf_size[0] / 2, bf_y, bf_h / 2 + 0.04), M["concrete"])
for sy in (-1, 1):
    box(f"bio_wall_y{sy:+d}", "water", (bf_size[0] + 0.06, 0.06, bf_h), (bf_x, bf_y + sy * bf_size[1] / 2, bf_h / 2 + 0.04), M["concrete"])
box("bio_base", "water", (bf_size[0], bf_size[1], 0.06), (bf_x, bf_y, 0.07), M["concrete"])
z = 0.1
for name, m, h in (("bio_gravel", M["gravel"], 0.25), ("bio_sand", M["sand"], 0.18), ("bio_topsoil", M["topsoil"], 0.15)):
    box(name, "water", (bf_size[0] - 0.06, bf_size[1] - 0.06, h), (bf_x, bf_y, z + h / 2), m)
    z += h
for k in range(8):
    tuft(f"bio_plant_{k}", "water", (bf_x + random.uniform(-0.6, 0.6), bf_y + random.uniform(-0.45, 0.45), z), 0.5, M["plant"])
col = (2.4, -0.7, 1.0)
box("collector", "water", (0.4, 0.4, 0.35), col, M["grey_pipe"])
under = PILE_H - 0.15  # cota de tuberías bajo las vigas
pipe("grey_shower", "water", [(sh_cx, sh_cy, FLOOR_Z + 0.05), (sh_cx, sh_cy, under), (col[0], col[1], under), (col[0], col[1], col[2] + 0.18)], M["grey_pipe"])
pipe("grey_sink", "water", [(skx, iy - 0.21, fz + 0.6), (skx, iy - 0.21, under - 0.1), (col[0], iy - 0.21, under - 0.1),
                             (col[0], col[1] + 0.15, under - 0.1), (col[0], col[1] + 0.15, col[2] + 0.18)], M["grey_pipe"])
pipe("grey_to_filter", "water", [(col[0], col[1], col[2] - 0.18), (col[0], col[1], 0.9), (bf_x + 0.4, bf_y - 0.2, 0.9), (bf_x + 0.4, bf_y - 0.2, z + 0.05)], M["grey_pipe"])
pipe("filter_to_tank", "water", [(bf_x + bf_size[0] / 2, bf_y, 0.18), (0.6, bf_y, 0.18), (0.6, PIT_Y, 0.18),
                                  (tank_x - TANK[0] / 2 + 0.2, PIT_Y, 0.18), (tank_x - TANK[0] / 2 + 0.2, PIT_Y, tz + TANK[2] + 0.05)],
     M["grey_pipe"])
pipe("treated_suction", "water", [(tank_x + TANK[0] / 2, PIT_Y, tz + 0.2), (pump_x - 0.16, PIT_Y, tz + 0.2)], M["green_pipe"])
pipe("treated_rise", "water", [(pump_x, PIT_Y, tz + 0.34), (pump_x, PIT_Y, under + 0.05), (pump_x, iy - 0.09, under + 0.05),
                                (tx, iy - 0.09, under + 0.05), (tx, iy - 0.09, fz + 0.5)], M["green_pipe"])

# ---------------------------------------------------------------- UV por proyección de caja


def box_uv(ob):
    me = ob.data
    if not me.materials:
        return
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    mw = ob.matrix_world
    rot = mw.to_3x3()
    world = [mw @ v.co for v in bm.verts]
    lo = Vector((min(c.x for c in world), min(c.y for c in world), min(c.z for c in world)))
    hi = Vector((max(c.x for c in world), max(c.y for c in world), max(c.z for c in world)))
    for f in bm.faces:
        m = me.materials[f.material_index] if f.material_index < len(me.materials) else None
        if m is None:
            continue
        n = rot @ f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        tile = TILE.get(m.name)
        for loop in f.loops:
            co = mw @ loop.vert.co
            if m.name == "pv_cell":  # una grilla completa por panel
                loop[uv].uv = ((co.x - lo.x) / (hi.x - lo.x), (co.y - lo.y) / (hi.y - lo.y))
            elif tile:
                loop[uv].uv = (co[a] / tile, co[b] / tile)
    bm.to_mesh(me)
    bm.free()


bpy.context.view_layer.update()
empty = [ob.name for ob in bpy.data.objects if ob.type == "MESH" and not ob.data.vertices]
for name in empty:  # p. ej. un corte que no alcanzó geometría
    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
print("mallas vacías eliminadas:", empty)
for ob in bpy.data.objects:
    if ob.type == "MESH":
        box_uv(ob)
        for poly in ob.data.polygons:
            poly.use_smooth = False

# ---------------------------------------------------------------- cámara/luz de preview
bpy.ops.object.light_add(type="SUN", location=(5, -5, 10), rotation=(math.radians(50), 0, math.radians(30)))
bpy.context.active_object.data.energy = 4
bpy.ops.object.camera_add(location=(17, -19, 12))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(64), 0, math.radians(42))
bpy.context.scene.camera = cam

# ---------------------------------------------------------------- export
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
for name in LAYERS:
    roots[name].select_set(True)
    for ch in roots[name].children_recursive:
        ch.select_set(True)
opts = dict(
    filepath=GLB_PATH,
    export_format="GLB",
    use_selection=True,
    export_draco_mesh_compression_enable=True,
    export_draco_mesh_compression_level=6,
    export_apply=True,
    export_yup=True,
)
try:
    bpy.ops.export_scene.gltf(**opts, export_image_format="WEBP", export_image_quality=80)
except TypeError:
    bpy.ops.export_scene.gltf(**opts, export_image_format="JPEG")
print({"glb": GLB_PATH, "bytes": os.path.getsize(GLB_PATH), "objects": len(bpy.data.objects)})
