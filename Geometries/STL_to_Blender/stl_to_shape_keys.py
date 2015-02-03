# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
   "name": "Import an STL Sequence Into Shape Keys",
   "author": "fercook",
   "version": (1, 0),
   "blender": (2, 6, 2),
   "api": 39685,
   "location": "File > Import-Export > STLs to Shape Keys",
   "description": "Import Multiple STLs into Shape Keys",
   "warning": "",
   "wiki_url": "",
   "tracker_url": "",
   "category": "Import-Export"}

# This Addon takes an object and adds a sequence of STL files as
# shape keys.

import bpy
import math
import glob
import os.path
import sys
import array
import os
from bpy.props import (BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty,
                       StringProperty,
                       CollectionProperty
                       )  
from bpy_extras.io_utils import ExportHelper, ImportHelper
from add_utils import AddObjectHelper, add_object_data
# Find out where the STL utils addon is located
for p in sys.path:
   if os.path.isdir(p+'/io_mesh_stl'):
       sys.path.append(p+'/io_mesh_stl')
import stl_utils


# -----------------------------------------------------------------------------
# Helper routines


# This routine switches the mesh of an object with a new one
# Transfering materials too
def switchMesh(obj,newMesh): 
   oldMesh = obj.data
   oldMeshName = oldMesh.name   
   for mat in oldMesh.materials:
       newMesh.materials.append(mat)
   obj.data = newMesh
   oldMesh.user_clear()
   bpy.data.meshes.remove(oldMesh)
   newMesh.name = oldMeshName

def loadSTL(path,name):
   faces, verts = stl_utils.read_stl(path)
   # Create new mesh
   mesh = bpy.data.meshes.new(name)
   # Make a mesh from a list of verts/edges/faces.
   mesh.from_pydata(verts, [], faces)
   # Do I need to update mesh geometry after adding stuff?
   mesh.validate()
   mesh.update()
   return mesh

# File manipulation routines
EXT_LIST = {
    'stl': ('stl', 'stlb')
    }

EXTENSIONS = [ext for ext_ls in EXT_LIST.values() for ext in ext_ls]

def is_stl_fn_any(fn):
    ext = os.path.splitext(fn)[1].lstrip(".").lower()
    return ext in EXTENSIONS

def is_stl_fn_single(fn, ext_key):
    ext = os.path.splitext(fn)[1].lstrip(".").lower()
    return ext in EXT_LIST[ext_key]

def generate_paths(self):
    directory, fn = os.path.split(self.filepath)
    if fn and not self.all_in_directory:
        # test for extension
        if not is_stl_fn_any(fn):
            return [], directory

        return [self.filepath], directory

    if not fn or self.all_in_directory:
        stlpaths = []
        files_in_directory = os.listdir(directory)
        # clean files from non STLs
        files_in_directory = [fn for fn in files_in_directory
                              if is_stl_fn_any(fn)]
        # clean from unwanted extensions
        if self.extension != "*":
            files_in_directory = [fn for fn in files_in_directory
                                  if is_stl_fn_single(fn, self.extension)]
        # create paths
        for fn in files_in_directory:
            stlpaths.append(os.path.join(directory, fn))

        return stlpaths, directory



# -----------------------------------------------------------------------------
# Main

def import_stls(self, context):
    basisobj = bpy.context.active_object
    if (basisobj != None or not self.addtoselection):
        import_list = self.paths
        print ("holaaaa")
        for jo in import_list:
            print (jo)
        print ("chau")
        NumShapes = len(import_list)
        if (not self.addtoselection):
            # We load the first file in the list
            # and it becomes the basis object
            objName="STLSequence"
            basismesh = loadSTL(import_list[0], objName)
            # Load object into scene
            scene = bpy.context.scene
            basisobj = bpy.data.objects.new(objName, basismesh)
            scene.objects.link(basisobj)
            #import_list.pop(0) # We remove the basis so it does not become a shape key
        # We create a temporary object to store the meshes one by one
        tmpName="TemporarySTL"
        tmpMesh = loadSTL(import_list[0], tmpName)
        # Load tmp object into scene
        scene = bpy.context.scene
        tmpobj = bpy.data.objects.new(tmpName, tmpMesh)
        scene.objects.link(tmpobj)
        # And since we are at it, we add the first shape key
        basisobj.select = True
        bpy.context.scene.objects.active = basisobj
        tmpobj.select = True
        bpy.ops.object.join_shapes()
        tmpobj.select=False
        import_list.pop(0) # We remove the first item since we did it manually
        for path in import_list:
            tmpMesh = loadSTL(path,tmpName)
            switchMesh(tmpobj,tmpMesh) # Save memory by discarding last loaded mesh
            basisobj.select = True
            bpy.context.scene.objects.active = basisobj
            tmpobj.select = True
            bpy.ops.object.join_shapes()
            tmpobj.select=False
        if (self.keyframe):
            # Finally keyframe the newly added shapes
            shapes = basisobj.data.shape_keys.key_blocks[-NumShapes:]
            for frame_index in range(0,NumShapes):
                cur_frame = self.iniframe+self.keyevery*frame_index
                shapes[frame_index].value = 0.0
                shapes[frame_index].keyframe_insert(data_path="value",frame=cur_frame-self.keyevery)
                shapes[frame_index].keyframe_insert(data_path="value",frame=cur_frame+self.keyevery)
                shapes[frame_index].value = 1.0
                shapes[frame_index].keyframe_insert(data_path="value",frame=cur_frame)
        # Try to delete the temp object
        tmpobj.select = True
        basisobj.select = False
        context.scene.objects.active = tmpobj
        bpy.ops.object.delete()
                    
    context.scene.update()
    self.report({'INFO'}, "Added %i Shape Keys(s)" % NumShapes)
                                



class STLSequenceToShapeKey(bpy.types.Operator, ImportHelper, AddObjectHelper):
   """Import STLs as Shape Keys"""
   bl_idname = "import_mesh.stlshp"
   bl_label = "STLs to Shape Keys"
   bl_description = "Adds a sequence of STL files as shape keys"
   bl_options = {'REGISTER', 'UNDO'}

   filename_ext = ".stl"
   # 
   filter_glob = StringProperty(
       default="*.stl",
       options={'HIDDEN'},
       )
   files = CollectionProperty(
       name="File Path",
       type=bpy.types.OperatorFileListElement,
       )
   directory = StringProperty(
       subtype='DIR_PATH',
       )

    # -------
    # Options
   all_in_directory = BoolProperty(
            name="All in directory",
            description=("Import all STL files in this directory"),
            default=False,
            )
   keyframe = BoolProperty(
            name='Create Keyframes',
            description='Keyframe the Shape Keys after addition',
            default=True,
            )
   keyevery = IntProperty(name="Keyframe step",
            description="Frame spacing between keyframes",
            min=1,
            default=1,
            )
   iniframe = IntProperty(name="Initial Frame",
            description="Start Keyframinf from this frame on",
            min=1,
            default=1,
            )
   extension = EnumProperty(
            name="Extension",
            description="Only import files of this type",
            items=(
            ('stl', 'STL (.stl)', 'Standard Titurri Luxury'),
            ('stlb', 'STLB (.stlb)', 'Buinary Standard Titurri Luxury')),            
            )
   addtoselection = BoolProperty(
            name='Add to Selected',
            description='Adds the STLs files as new Shape Keys of selected object',
            default=False,
            )            
   relative = BoolProperty(
            name="Relative",
            description="Apply relative paths",
            default=True,
            )

   def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label("File Options:", icon='FILTER')
        box.prop(self, "all_in_directory")
        box.prop(self, "extension", icon='FILE_IMAGE')

        row = box.row()
        row.active = bpy.data.is_saved
        row.prop(self, "relative")

        box = layout.box()
        box.label("Import Options:", icon='FILTER')
        box.prop(self, "keyframe")
        box.prop(self, "iniframe")        
        box.prop(self, "keyevery")
        box.prop(self, "addtoselection")

   def execute(self,context):

        if not bpy.data.is_saved:
            self.relative = False

        self.paths = [os.path.join(self.directory, name.name)
                for name in self.files]

        if not self.paths:
            self.paths.append(self.filepath)
        # Copied from a similar plugin:
        # the add utils don't work in this case
        # because many objects are added
        # disable relevant things beforehand
        editmode = context.user_preferences.edit.use_enter_edit_mode
        context.user_preferences.edit.use_enter_edit_mode = False
        if context.active_object\
        and context.active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        import_stls(self, context)

        context.user_preferences.edit.use_enter_edit_mode = editmode
        return {'FINISHED'}


# Blender boilerplate to incorporate into the UI

def menu_import(self, context):
   self.layout.operator(STLSequenceToShapeKey.bl_idname,
                        text="STLs to Shape Key(.stl)")
def register():
   bpy.utils.register_module(__name__)
   bpy.types.INFO_MT_file_import.append(menu_import)

def unregister():
   bpy.utils.unregister_module(__name__)
   bpy.types.INFO_MT_file_import.remove(menu_import)

if __name__ == "__main__":
   register()

