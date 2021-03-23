# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "MMDBridge Material Importer",
    "author" : "Vwings",
    "description" : "Import and apply MMDBridge Materails(.mtl).",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 3),
    "location" : "File > Import",
    "warning" : "",
    "category" : "Import-Export"
}

import bpy

from .import_mtl_op import IMPORT_OT_MMDBridgeMaterialImport

classes = (
    IMPORT_OT_MMDBridgeMaterialImport,
)

# ui
def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_MMDBridgeMaterialImport.bl_idname, text='MMDBridge Material (.mtl)', icon='OUTLINER_OB_ARMATURE')
    

def register():
    for cls in classes:
        print(cls)
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
