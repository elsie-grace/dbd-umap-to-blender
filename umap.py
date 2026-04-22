import bpy
import json
import math
import os

# ---- SETTINGS ----

# ueformat uses 0.01 as default scale
SCALE = 0.01
# lights were a bit too dim, so I tried * 10, might need more
LIGHT_POWER_MULTIPLIER = 10
# planes have strange orientation, you may enable it but you might have to rotate them manually
ENABLE_PLANES = False
# export .umap as .json and specify the path to it
JSON_PATH = r"G:\FModel\Export\DeadByDaylight\Content\Maps\LobbyKetchup.json"
# same as FModel export directory
MESH_FOLDER = r"G:\FModel\Export"

# ---- SCRIPT ----

actors_data = {}

lights_type_map = {
    "PointLightComponent": "POINT",
    "SpotLightComponent": "SPOT",
    "RectLightComponent": "AREA",
    "DirectionalLightComponent": "SUN"
}

def drop_last_name_part(name):
    return ".".join(name.split(".")[:-1])

def add_dicts(d1, d2):
    result = {}
    for key in d1:
        result[key] = d1.get(key, 0) + d2.get(key, 0)
    return result

def mult_dicts(d1, d2):
    result = {}
    for key in d1:
        result[key] = d1.get(key, 0) * d2.get(key, 0)
    return result

def get_name_full(props):
    return props.get("ObjectName")

def get_name_without_type(props):
    fullname = get_name_full(props)

    if "'" in fullname:
        return fullname.split("'")[1]
    else:
        return fullname
    
def get_data_name(props):
    name = get_name_without_type(props)
    return drop_last_name_part(name)

def rotate_vector_by_rotation(vec, rot):
    pitch = math.radians(rot.get("Pitch", 0))
    yaw = math.radians(rot.get("Yaw", 0))
    roll = math.radians(rot.get("Roll", 0))
    
    x, y, z = vec.get("X", 0), vec.get("Y", 0), vec.get("Z", 0)
    
    cos_roll, sin_roll = math.cos(roll), math.sin(roll)
    y1 = y * cos_roll - z * sin_roll
    z1 = y * sin_roll + z * cos_roll
    y, z = y1, z1
    
    cos_pitch, sin_pitch = math.cos(pitch), math.sin(pitch)
    x1 = x * cos_pitch + z * sin_pitch
    z1 = -x * sin_pitch + z * cos_pitch
    x, z = x1, z1
    
    cos_yaw, sin_yaw = math.cos(yaw), math.sin(yaw)
    x1 = x * cos_yaw - y * sin_yaw
    y1 = x * sin_yaw + y * cos_yaw
    x, y = x1, y1
    
    return {"X": x, "Y": y, "Z": z}

def get_location(actor):
    props = actor.get("Properties", {})
    if props == None:
        return { "Y": 0, "X": 0, "Z": 0 }

    loc = props.get("RelativeLocation", { "Y": 0, "X": 0, "Z": 0 })

    parentdata = props.get("AttachParent")
    if parentdata != None:
        if get_data_name(parentdata) != get_name_without_type(actor.get("Outer")):
            parent = actors_data.get(get_data_name(parentdata))
            if parent != None:
                parent_loc = get_location(parent)
                parent_rot = get_rotation(parent)
                parent_scale = get_scale(parent)
                
                scaled_loc = mult_dicts(loc, parent_scale)
                rotated_loc = rotate_vector_by_rotation(scaled_loc, parent_rot)
                
                return add_dicts(rotated_loc, parent_loc)

    return loc

def get_rotation(actor):
    props = actor.get("Properties", {})

    if props == None:
        return { "Pitch": 0, "Yaw": 0, "Roll": 0 }
    
    rot = props.get("RelativeRotation", { "Pitch": 0, "Yaw": 0, "Roll": 0 })

    parentdata = props.get("AttachParent")
    if parentdata != None:
        if get_data_name(parentdata) != get_name_without_type(actor.get("Outer")):
            parent = actors_data.get(get_data_name(parentdata))
            if parent != None:
                return add_dicts(rot, get_rotation(parent))

    return rot

def get_scale(actor):
    props = actor.get("Properties", {})

    if props == None:
        return { "Y": 1, "X": 1, "Z": 1 }
    
    scale = props.get("RelativeScale3D", { "Y": 1, "X": 1, "Z": 1 })

    parentdata = props.get("AttachParent")
    if parentdata != None:
        if get_data_name(parentdata) != get_name_without_type(actor.get("Outer")):
            parent = actors_data.get(get_data_name(parentdata))
            if parent != None:
                return mult_dicts(scale, get_scale(parent))

    return scale

def unreal_to_blender_location(loc):
    return (loc.get("X", 0) * SCALE, -loc.get("Y", 0) * SCALE, loc.get("Z", 0) * SCALE)

def unreal_to_blender_rotation(rot):
    pitch = math.radians(rot.get("Pitch", 0))
    yaw = math.radians(-rot.get("Yaw", 0))
    roll = math.radians(rot.get("Roll", 0))
    return (pitch, roll, yaw)

def unreal_to_blender_scale(scale):
    return (scale.get("X", 1), scale.get("Y", 1), scale.get("Z", 1))

mesh_cache = {}
def load_mesh(mesh_name):
    if mesh_name in mesh_cache:
        return mesh_cache[mesh_name]

    mesh_name = mesh_name.replace("/Game/", "DeadByDaylight/Content/")
    if mesh_name == "/Engine/BasicShapes/Plane":
        if ENABLE_PLANES:
            return create_plane()
        else:
            return None

    path = os.path.join(MESH_FOLDER, mesh_name.replace("/", "\\") + ".uemodel")
    if not os.path.exists(path):
        print(f"Missing mesh: {mesh_name}. Tried {path}")
        return None

    before = set(bpy.data.objects)

    bpy.ops.uf.import_uemodel(
        directory = os.path.dirname(path),
        files=[{"name": os.path.basename(path)}]
    )
    
    after = set(bpy.data.objects)
    new_objects = list(after - before)
    
    mesh_cache[mesh_name] = new_objects
    return new_objects

def create_plane():
    before = set(bpy.data.objects)
    bpy.ops.mesh.primitive_plane_add()
    after = set(bpy.data.objects)
    new_objects = list(after - before)
    return new_objects

def import_mesh(actor):
    props = actor.get("Properties", {})
    mesh_path = props.get("StaticMesh")

    if not mesh_path:
        return

    mesh_name = mesh_path["ObjectPath"].split(".")[0]

    imported = load_mesh(mesh_name)
    if not imported:
        return

    for obj in imported:
        obj.location = unreal_to_blender_location(get_location(actor))
        obj.rotation_euler = unreal_to_blender_rotation(get_rotation(actor))
        obj.scale = unreal_to_blender_scale(get_scale(actor))
        obj.name = get_name_full(actor.get("Outer", {}))
    
    return obj
        
def import_light(actor):
    actor_type = actor.get("Type")
    props = actor.get("Properties", {})

    if actor_type not in lights_type_map:
        return None

    light_data = bpy.data.lights.new(name=actor_type, type=lights_type_map[actor_type])
    light_obj = bpy.data.objects.new(name=actor_type, object_data=light_data)
    bpy.context.collection.objects.link(light_obj)

    light_obj.location = unreal_to_blender_location(get_location(actor))
    light_obj.rotation_euler = unreal_to_blender_rotation(get_rotation(actor))

    intensity = props.get("Intensity", 1000)

    light_data.energy = intensity * LIGHT_POWER_MULTIPLIER

    color = props.get("LightColor", {"R": 255, "G": 255, "B": 255})
    light_data.color = (
        color["R"] / 255,
        color["G"] / 255,
        color["B"] / 255
    )

    if actor_type == "SpotLightComponent":
        inner = props.get("InnerConeAngle", 30)
        outer = props.get("OuterConeAngle", 45)
        light_data.spot_size = math.radians(outer)
        light_data.spot_blend = 1 - (inner / outer if outer != 0 else 0)
        
        cone_factor = max(0.01, (outer / 45.0) ** 2)
        light_data.energy = light_data.energy * cone_factor
        
    light_obj.name = get_name_full(actor.get("Outer", {}))

    return light_obj

with open(JSON_PATH, "r") as f:
    data = json.load(f)

for actor in data:
    actor_type = actor.get("Type")
    
    if actor_type in ["StaticMeshComponent"]:
        actors_data[get_name_without_type(actor.get("Outer"))] = actor
        continue
    
    if actor_type in ["PointLightComponent", "SpotLightComponent", "RectLightComponent", "DirectionalLightComponent"]:
        actors_data[get_name_without_type(actor.get("Outer"))] = actor
        continue

for actor in data:
    actor_type = actor.get("Type")
    
    if actor_type in ["StaticMeshComponent"]:
        import_mesh(actor)
        continue
    
    if actor_type in ["PointLightComponent", "SpotLightComponent", "RectLightComponent", "DirectionalLightComponent"]:
        import_light(actor)
        continue