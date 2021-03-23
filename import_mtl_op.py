import bpy
from bpy_extras.io_utils import ImportHelper

import os

class IMPORT_OT_MMDBridgeMaterialImport(bpy.types.Operator, ImportHelper):
    bl_idname = "mmdbridge.import_material"
    bl_label = "Import MMDBridge Material(.mtl)"
    bl_description = "Import MMDBridge exported Material(.mtl)"
    bl_options = {'PRESET'}

    filename_ext = ".mtl"
    filter_glob = bpy.props.StringProperty(default='*.mtl', options={'HIDDEN'})
    filepath = bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN'})

    # options
    limit_to_visible = bpy.props.BoolProperty(name='Limit to visible objects', default=True)
    overwrite_existing_materials = bpy.props.BoolProperty(name='Overwrite existing materials', default=True)
    merge_same_textures = bpy.props.BoolProperty(name='Merge same texures to one material', default=True)
    search_paths = bpy.props.StringProperty(
        name='Texture Dir',
        description='Set addtional texture directories. If there are more than one, separate by comma.'
    )

    _image_load_cache = {}
    _search_dirs = []
    _material_cache = {}

    def execute(self, context):
        self.init()
        self.import_mmdbridge_material()
        self.assign_materials()
        return {'FINISHED'}

    def init(self):
        self._search_dirs = [os.path.dirname(self.filepath)]
        # init search location
        if self.search_paths != '':
            self._search_dirs.extend(self.search_paths.split(','))

        # clear caches before each run
        self._material_cache = {}
        self._image_load_cache = {}

    def import_mmdbridge_material(self):
        if self.filepath is None:
            print('Please select a mtl file...')
            return {'CANCELED'}

        # {object_name: {base_color: 'xxx.png', material_name: 'xxxx'}}
        object_material = {}
        current_object_name = None

        mtl_file = open(self.filepath, 'r')
        for line in mtl_file.readlines():
            words = line.split();
            if len(words) < 2:
                continue
            elif 'newmtl' in words[0]:
                material_splits = words[1].split('_')
                object_index = material_splits[1]
                material_index = material_splits[2]
                object_name = 'xform_'+ object_index + '_material_' + material_index
                object_material[object_name] = {}
                current_object_name = object_name
            elif 'map_Kd' in words[0]:
                texture_path = words[1]
                object_material[current_object_name]['base_color'] = texture_path

                if self.merge_same_textures:
                    path_segments = texture_path.split('/')
                    image_file_name = path_segments[len(path_segments) - 1]
                    material_name = image_file_name.split('.')[0]
                    object_material[current_object_name]['material_name'] = material_name

        self.object_material = object_material

    def assign_materials(self):
        # get all available objects
        all_object_names = [
            obj.name 
            for obj in bpy.data.objects 
            if obj.type == 'MESH' and (obj.visible_get() if self.limit_to_visible else True)
        ]

        for object_name, material_info in self.object_material.items():
            if object_name in all_object_names:
                # check if obj already has active materials 
                if not self.overwrite_existing_materials:
                    if len([m for m in bpy.data.objects[object_name].material_slots if len(m.name) > 0]) > 0:
                        continue
                
                # Get material begin

                material_name = object_name
                if 'material_name' in material_info:
                    material_name = material_info['material_name']

                mat = None
                if material_name in self._material_cache:
                    mat = self._material_cache[material_name]
                else:
                    mat = bpy.data.materials.get(material_name)
                    if mat is not None:
                        bpy.data.materials.remove(mat)
                    # create material
                    mat = bpy.data.materials.new(name=material_name)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                
                    image_texture = nodes.new(type='ShaderNodeTexImage')
                    image_texture.location = -500,300
                    
                    # load images
                    image = self.get_image(material_info['base_color'])
                    if image is not None:
                        image_texture.image = image

                    principled = nodes.get('Principled BSDF')
                    material_output = nodes.get('Material Output')
                    material_output.location = 700,300

                    transparent_node = nodes.new(type='ShaderNodeBsdfTransparent')
                    transparent_node.location = 100,450

                    mix_shader_node = nodes.new(type='ShaderNodeMixShader')
                    mix_shader_node.location = 400,300

                    links.new(image_texture.outputs[0], principled.inputs[0])
                    links.new(image_texture.outputs[1], mix_shader_node.inputs[0])
                    links.new(transparent_node.outputs[0], mix_shader_node.inputs[1])
                    links.new(principled.outputs[0], mix_shader_node.inputs[2])
                    links.new(mix_shader_node.outputs[0], material_output.inputs[0])

                    mat.blend_method = 'HASHED'
                    mat.shadow_method = 'HASHED'
                    
                    self._material_cache[material_name] = mat

                # Get material end

                # Assign it to object
                # get the obj
                if mat is None:
                    continue

                obj = bpy.data.objects[object_name]
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)

    def get_image(self, name):
        # load from cache
        image = None
        if name not in self._image_load_cache:
            # load from file system...
            for search_dir in self._search_dirs:
                image_file = os.path.join(search_dir, name) 
                try:
                    image = bpy.data.images.load(image_file)
                    self._image_load_cache[name] = image
                    break
                except:
                    pass
            if image is None:
                print('Cannot load image: ' + name)
        else:
            image = self._image_load_cache[name]

        return image