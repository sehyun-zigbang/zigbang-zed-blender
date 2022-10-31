import bpy

#------------------------------------
# Scene Clear
def clear():
    for c in bpy.data.collections:
        bpy.data.collections.remove(c)
    for o in bpy.context.scene.collection.objects:
        bpy.data.objects.remove(o)
    for m in bpy.data.materials:
        bpy.data.materials.remove(m)
    for m in bpy.data.meshes:
        bpy.data.meshes.remove(m)
    for i in bpy.data.images:
        if not ".hdr" in i.name:
            bpy.data.images.remove(i)
            
#------------------------------------
# calculate bound box

from mathutils import Vector
from functools import reduce
from itertools import product

def merge_boxes(objects):
    return reduce(lambda x, y: x + y,
        [Box(obj) for obj in objects if obj.type == 'MESH'])

class Box:
    def __init__(self, bl_object=None, max_min=None):
        if bl_object and bl_object.type == 'MESH':
            self.__bound_box = self.__get_bound_box_from_object(bl_object)
        elif max_min:
            self.__bound_box = self.__get_bound_box_from_max_min(max_min)
        else:
            raise TypeError()

    def __add__(self, bound_box):
        return self.merge(bound_box)

    def __getitem__(self, index):
        return self.__bound_box[index]

    @property
    def max(self):
        return Vector(max((v.x, v.y, v.z) for v in self.__bound_box))

    @property
    def min(self):
        return Vector(min((v.x, v.y, v.z) for v in self.__bound_box))

    @property
    def center(self):
        return sum((v for v in self.__bound_box), Vector()) / 8

    def merge(self, box):
        if not box:
            return self

        if not isinstance(box, Box):
            raise TypeError('Require a Box object')

        max_new = Vector(map(max, zip(self.max, box.max)))
        min_new = Vector(map(min, zip(self.min, box.min)))

        return Box(max_min = (max_new, min_new))

    def __get_bound_box_from_object(self, bl_object):
        return [bl_object.matrix_world @ Vector(v) \
                for v in bl_object.bound_box]

    def __get_bound_box_from_max_min(self, max_min):
        max_point, min_point = max_min

        return [Vector(v) for v in product((max_point.x, min_point.x),
                                           (max_point.y, min_point.y),
                                           (max_point.z, min_point.z))]


#------------------------------------
# Generate
import json
import math
import bmesh
import glob
import os
import uuid

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)
        
def execute():
    
    path = bpy.path.abspath("//")
    
    source_path = "{}/source/source.blend".format(path)
   
    input_path = "{}/inputs".format(path)
    file_names = glob.glob("{}/*.json".format(input_path))
    
    for file_name in file_names:
         clear()
        
         with open(file_name, 'r') as file:
             dict = json.load(file)
         
         danji_id = dict["DanjiId"]
         room_type_id = dict["RoomTypeId"]
         level = dict["Level"]
         
         #------------------------------------
         # Generate Collections
         model_name = "{}_{}_{}".format(danji_id, room_type_id, level)
         
         glTf_path = "{}/assets/glTF".format(path)
         danji_path = '{}/{}'.format(glTf_path, danji_id)
         room_path = '{}/{}'.format(danji_path, room_type_id)
         createFolder(glTf_path)
         createFolder(danji_path)
         createFolder(room_path)
             
         collection_generate = bpy.data.collections.new(model_name)
         bpy.context.scene.collection.children.link(collection_generate)
        
         collection_frame = bpy.data.collections.new("frame")
         collection_furniture = bpy.data.collections.new("furnitures")
         collection_window = bpy.data.collections.new("windows")
         collection_door= bpy.data.collections.new("doors")
         collection_light= bpy.data.collections.new("lights")
         
         collection_generate.children.link(collection_frame)
         collection_generate.children.link(collection_furniture)
         collection_generate.children.link(collection_window)
         collection_generate.children.link(collection_door)
         collection_generate.children.link(collection_light)
        
         #------------------------------------
         # Generate Furnitures
         for furniture in dict["Furnitures"]:
             name = furniture["name"]
             type = furniture["type"]
            
             position = furniture["position"]
             px = round(position["x"], 2)
             py = round(position["y"], 2) + 0.1
             pz = round(position["z"], 2)
            
             rotation = furniture["rotation"]
             rx = math.radians(round(rotation["x"]))
             ry = math.radians(round(rotation["y"]))
             rz = math.radians(round(rotation["z"]))
            
             scale = furniture["scale"]
             sx = round(scale["x"], 2)
             sy = round(scale["y"], 2)
             sz = round(scale["z"], 2)
                             
             bpy.ops.wm.append(filepath = os.path.join(source_path, "Object", name), directory=os.path.join(source_path, "Object"), filename=name)
             if bpy.data.objects.get(name):
                 obj = bpy.data.objects[name]
                 obj.location = (px, py, pz)
                 obj.rotation_euler = (rx, ry, rz)
                 obj.scale = (sx, sy, sz)
             else:
                 bpy.ops.mesh.primitive_cube_add()
                 obj = bpy.context.object
                 obj.location = (px, py + sy/2, pz)
                 obj.rotation_euler = (rx, ry, rz)
                 obj.scale = (sx/2, sy/2, sz/2)
                 
             obj.name = "{}_{}".format(name, uuid.uuid1())
            
             if type == 0 :
                 collection_furniture.objects.link(obj)
             elif type == 1:
                 collection_window.objects.link(obj)
             elif type == 2:
                 collection_door.objects.link(obj)
                 
         #------------------------------------
         # Generate Wall & Floors   
         for data in dict["WallAndFloors"]:
             name = data["name"]
            
             #if "Roof" in name:
              #   continue
            
             vertices = data["vertices"]
             verts = []
             for v in vertices:
                 vx = round(v["x"], 2)
                 vy = round(v["y"], 2)
                 vz = round(v["z"], 2)
                 verts.append((vx, vy, vz))
            
             triangles = data["triangles"]
            
             edges = []
             faces = []
             for i in range(0, len(triangles), 3):
                 faces.append(triangles[i:i+3])
            
             uv_datas = data["uv"]
             uvs = []
             for uv in uv_datas:
                 ux = round(uv["x"],2)
                 uy = round(uv["y"],2)
                 uvs.append([ux, uy])
             
             mesh = bpy.data.meshes.new(name)  
             mesh.from_pydata(verts, edges, faces)
             mesh.calc_loop_triangles()
             mesh.calc_normals_split()
             mesh.update(calc_edges=True)
             
             
             obj = bpy.data.objects.new(name, mesh)
             
             if not bpy.data.materials.get(name):
                 bpy.ops.wm.append(filepath = os.path.join(source_path, "Material", name), directory=os.path.join(source_path, "Material"), filename=name)
                 
             if bpy.data.materials.get(name):
                obj.active_material = bpy.data.materials[name]
             
             obj.name = "{}_{}".format(obj.name,uuid.uuid1())
             
             if name.startswith("Floor_"):
                 collection_frame.objects.link(obj)
                 if "Roof" in name:
                     bpy.context.view_layer.objects.active = obj
                     obj.select_set(True)
                     obj.location = (0, -0.1, 0)
                     bpy.ops.object.modifier_add(type='SOLIDIFY')
                     bpy.context.object.modifiers["Solidify"].thickness = 50
                     bpy.context.object.modifiers["Solidify"].offset = -1
                     bpy.ops.object.convert(target='MESH')
                     obj.select_set(False)
                 else:
                     obj.location = (0, 0.1, 0)
             else:
                 collection_frame.objects.link(obj)
                 if "Edge_Top" in name:
                     bpy.context.view_layer.objects.active = obj
                     obj.select_set(True)
                     obj.location = (0, -0.2, 0)
                     bpy.ops.object.modifier_add(type='SOLIDIFY')
                     bpy.context.object.modifiers["Solidify"].thickness = -3
                     bpy.context.object.modifiers["Solidify"].offset = -1
                     bpy.ops.object.convert(target='MESH')
                     obj.select_set(False)
                 if "Edge_Bottom" in name:
                     bpy.context.view_layer.objects.active = obj
                     obj.select_set(True)
                     obj.location = (0, -0.1, 0)
                     bpy.ops.object.modifier_add(type='SOLIDIFY')
                     bpy.context.object.modifiers["Solidify"].thickness = -3
                     bpy.context.object.modifiers["Solidify"].offset = -1
                     bpy.ops.object.convert(target='MESH')
                     obj.select_set(False)
                    
             
             #------------------------------------
             # Generate UV     
             context = bpy.context
             scene = context.scene
             vl = context.view_layer
             vl.objects.active = obj
             
             obj.select_set(True)
             
             ob = context.object
             me = obj.data
             
             if len(obj.data.uv_layers) == 0:
                     uvlayer = me.uv_layers.new(name=obj.name)
                     me.uv_layers.active = uvlayer
                     for tri in me.loop_triangles:
                         if obj.name.startswith("Wall"):
                             if "Bathroom" in obj.name or "Gate" in obj.name or "Balcony" in obj.name:
                                 obj.location = (0, 1, 0)
                                 for i in range(3):
                                    vert_index = tri.vertices[i]
                                    loop_index = tri.loops[i]
                                    uvlayer.data[loop_index].uv = (uvs[vert_index][0], uvs[vert_index][1])                 
                             else:
                                 new_uvs = []
                                 for i in range(3):
                                     vert_index = tri.vertices[i]
                                     vert = verts[vert_index]
                                     new_uv = [0, 0]
                                     if vert[1] == 0:
                                         new_uv[1] = 0
                                     else:
                                         new_uv[1] = 1;
                                     new_uvs.append(new_uv)

                                 vert1 = verts[tri.vertices[0]]
                                 vert2 = verts[tri.vertices[1]]
                                 vert3 = verts[tri.vertices[2]]
                                 
                                 a = vert1[0] - vert2[0]
                                 b = vert1[2] - vert2[2]
                                 ver1to2_len = round(math.sqrt((a * a) + (b * b)))
                                 
                                 a = vert1[0] - vert3[0]
                                 b = vert1[2] - vert3[2]
                                 ver1to3_len = round(math.sqrt((a * a) + (b * b)))
                                 
                                 a = vert2[0] - vert3[0]
                                 b = vert2[2] - vert3[2]
                                 ver2to3_len = round(math.sqrt((a * a) + (b * b)))
                                 
                                 new_uvs[1][0] = ver1to2_len / 240
                                 new_uvs[2][0] = ver1to3_len / 240
                                 
                                 for i in range(3):
                                     loop_index = tri.loops[i]
                                     uvlayer.data[loop_index].uv = (new_uvs[i][0], new_uvs[i][1])
                                 
                         elif len(uvs) != 0:
                             for i in range(3):
                                 vert_index = tri.vertices[i]
                                 loop_index = tri.loops[i]
                                 uvlayer.data[loop_index].uv = (uvs[vert_index][0], uvs[vert_index][1])
         
         #------------------------------------
         # Center Positioning
         bpy.ops.object.select_all(action='SELECT')
         obj.select_set(True)
        
         bounds = merge_boxes(bpy.data.objects);
         center = bounds.center
         bpy.ops.transform.translate(value = (-center.x, 3, -center.z))
         bpy.ops.object.transform_apply(location = True, rotation=True, scale=True)
         
         obj.select_set(False)
         bpy.ops.object.select_all(action='DESELECT')
         
         #------------------------------------
         # 90 degree rotate. for Unity And Playfab .etc
         for ob in bpy.data.objects:
             if ob.parent == None:
                 ob.rotation_euler = (math.radians(90), 0, 0)
         
         bpy.ops.object.select_all(action='SELECT')
         obj.select_set(True)
         bpy.ops.object.transform_apply(location = True, rotation=True, scale=True)
         obj.select_set(False)
         bpy.ops.object.select_all(action='DESELECT')
         
         #------------------------------------
         # Genderate Area Light
         for ob in bpy.data.objects:
             if ob.name.startswith("Floor") and not "Roof" in ob.name:
                bounds = Box(ob)
                center = bounds.center
                size = bounds.max - bounds.min
                
                bpy.ops.object.light_add(type='AREA', align='WORLD', location=(center.x, center.y, 200))
                light = bpy.context.object
                light.name = "Area.{}".format(ob.name)
                light.data.shape = 'RECTANGLE'
                light.data.energy = 5000
                light.data.diffuse_factor = 100
                light.data.specular_factor = 100
                light.data.volume_factor = 100
                light.data.size = size.x
                light.data.size_y = size.y
                collection_light.objects.link(bpy.context.object)
            
         #------------------------------------
         # Genderate Add Camera
         bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 3500), rotation=(0, -0, 0), scale=(1, 1, 1)) 
         camera = bpy.context.object
         scene.camera = camera
         camera.data.lens = 75
         camera.data.clip_end = 10000
         
         #------------------------------------
         # export glTF
         bpy.ops.export_scene.gltf(
         filepath='{}/{}.gltf'.format(room_path, model_name),
         export_texture_dir='{}/assets/textures'.format(path),
         
         check_existing = True, 
         export_format = 'GLTF_SEPARATE', 
#         export_format = 'GLB',
         export_image_format = 'JPEG', 
         export_copyright = 'Zigbang',
         
         #------------------------------------
         export_draco_mesh_compression_enable = True,
#         export_draco_mesh_compression_level = 6,
#         export_draco_position_quantization = 14,
#         export_draco_normal_quantization = 10;
#         export_draco_texcoord_quantization = 12,
#         export_draco_color_quantization = 10,
#         export_draco_generic_quantization = 12,

         #------------------------------------
#         export_keep_originals = False, 
#         export_texcoords = True, 
         export_normals = True,
#         export_tangents = True,
#         export_materials = 'EXPORT',
#         export_original_specular = False,
#         export_colors = True,
#         use_mesh_edges = True,
#         use_mesh_vertices = True,
         
         #------------------------------------
         export_cameras = True,
         export_animations = False,
         export_frame_range = False,
         export_force_sampling = False,
         export_nla_strips = False,
         export_def_bones = False,
         export_optimize_animation_size = False,
         export_anim_single_armature = False,
         export_current_frame = False,
         export_skins = False,
         export_all_influences = False,
         export_morph = False,
         export_morph_normal = False,
         export_morph_tangent = False,
         export_lights = True)
         
         # export_texture_dir
         #------------------------------------
         # Rendering
         render = bpy.context.scene.render;
         render.resolution_x = 1280
         render.resolution_y = 1280
         render.filepath = '{}/{}.png'.format(room_path, model_name)
         #bpy.ops.render.render(write_still = True)
         
    clear()
    return 0

#------------------------------------

execute()