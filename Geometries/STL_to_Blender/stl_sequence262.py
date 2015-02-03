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
   "name": "STL Sequence Loader",
   "author": "fercook",
   "version": (1, 3),
   "blender": (2, 6, 2),
   "api": 39685,
   "location": "File > Import-Export > STL Sequence ",
   "description": "Adds a STL Loader object",
   "warning": "",
   "wiki_url": "",
   "tracker_url": "",
   "category": "Import-Export"}

import bpy
import os
from bpy.props import StringProperty, BoolProperty, CollectionProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

# This Addon creates an object whose mesh is constantly reloaded
# (depending on the frame) from a series of STL files.

# This is the code that get's written to a new text window.
def code():
  """
import bpy
import math
import glob
import os.path
import sys
import array
from mathutils import Color 

# Find out where the STL utils addon is located
for p in sys.path:
   if os.path.isdir(p+'/io_mesh_stl'):
       sys.path.append(p+'/io_mesh_stl')
import stl_utils

# This routine switches the mesh of an object with a new one
# Transfering materials and UVs too
def switchMesh(obj,newMesh): 
   oldMesh = obj.data
   oldMeshName = oldMesh.name   
   oldmode='OBJECT'
   for mat in oldMesh.materials:
       newMesh.materials.append(mat)
   if (len(oldMesh.uv_textures)>0):
       if (hasattr(bpy.context,"active_object")):
           if (bpy.context.active_object.mode == 'EDIT'):
               oldmode='EDIT'
               bpy.ops.object.mode_set(mode='OBJECT')
       for uv in range(len(oldMesh.uv_textures)):
           newMesh.uv_textures.new()     
           for face in range(len(oldMesh.uv_textures[uv].data)): #:
               newMesh.uv_textures[uv].data[face].uv_raw = oldMesh.uv_textures[uv].data[face].uv_raw
               newMesh.uv_textures[uv].data[face].image = oldMesh.uv_textures[uv].data[face].image
   obj.data = newMesh
   oldMesh.user_clear()
   bpy.data.meshes.remove(oldMesh)
   newMesh.name = oldMeshName
   if (oldmode=='EDIT'):
       bpy.ops.object.mode_set(mode='EDIT')


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

def colorMesh(obj,mesh,colorFile):
   # Some defensive strategy
   if (not os.path.exists(colorFile)): # incorect file name
       return
   if (len(obj.material_slots) < 1):  # No material has been defined
       return
   if (len(obj.material_slots[0].material.texture_slots) < 1): # No textures have been defined
       return
   # If no ramp defined, create a default one
   if (not obj.material_slots[0].material.texture_slots[0].texture.use_color_ramp):
       obj.material_slots[0].material.texture_slots[0].texture.use_color_ramp = True
   ramp=obj.material_slots[0].material.texture_slots[0].texture.color_ramp
   if (len(mesh.vertex_colors) < 1): # Vertex colors are not active
       mesh.vertex_colors.new()
   valueList = readValueList(colorFile)
   if (obj["10 Fix Scale"]>0):
       minVal = obj["11 Min Value"]
       maxVal = obj["12 Max Value"]
   else:
       minVal = valueList[0][0]
       maxVal = valueList[0][1]
   if (len(valueList[1]) != 3*len(mesh.vertex_colors[0].data) or minVal == maxVal):
       return
   obj["11 Min Value"] = minVal
   obj["12 Max Value"] = maxVal
   # Color the vertices, hope they are in the same order as the originals
   for i in range(len(mesh.vertex_colors[0].data)):
       color1 = ramp.evaluate((valueList[1][3*i]-minVal)/(maxVal-minVal))[0:3]
       color2 = ramp.evaluate((valueList[1][3*i+1]-minVal)/(maxVal-minVal))[0:3]
       color3 = ramp.evaluate((valueList[1][3*i+2]-minVal)/(maxVal-minVal))[0:3]
       f = mesh.vertex_colors[0].data[i]
       f.color1 = color1
       f.color2 = color2
       f.color3 = color3

def readValueList(file):
    with open(file,"rb") as f:
        try: 
            numberOfFacets = array.array('i')
            header = array.array('b')            
            tailer = array.array('h')
            header.fromfile(f, 80)
            numberOfFacets.fromfile(f,1)
            data = [array.array('f'), array.array('f')]
            for facet in range(numberOfFacets[0]):
                rawdata = array.array('f') 
                rawdata.fromfile(f, 12) # Normal vector, and x,y,z of 3 vertices
                # Data is encoded as the x coordinate of the vertices
                data[1].append(rawdata[3])
                data[1].append(rawdata[6])
                data[1].append(rawdata[9])
                tailer.fromfile(f,1) # Load 2 bytes in the tail of the record
            # Min/Max is encoded in y,z coords    
            data[0].append(rawdata[4])
            data[0].append(rawdata[5])
        except EOFError: 
            print ("Cannot read Value file")
    return data

def onFrameChange(scene): 
   for obj in scene.objects:  
       if ("00 Active STL" in obj): # We search for STL loader objects
           current_frame = scene.frame_current # We do this anyway just in case
           if (obj["00 Active STL"]>0 and obj["06 Loaded Frame"] != current_frame):
               obj["06 Loaded Frame"] = current_frame # First thing: we block re-entry to the block
               start_frame = obj["03 Start Frame"]
               end_frame = obj["04 End Frame"]
               pathToSTLFiles = obj["01 Path"]
               fileNames = obj["02 File Names"]
               stl_files = sorted(glob.glob(os.path.join(pathToSTLFiles,fileNames+"*.stl"))) 
               if (len(stl_files)>0):
                   if (obj["05 Repeat"] > 0):
                       fileToLoad = int(math.fmod(current_frame-start_frame, len(stl_files)))
                   else:
                       if (current_frame < start_frame):
                           fileToLoad = 0
                       elif(current_frame > end_frame):
                           fileToLoad = len(stl_files)-1
                       else:
                           fileToLoad = int(min(current_frame-start_frame, end_frame-start_frame, len(stl_files)-1))
                   # We keep previous selection in case we are interactive
                   if (hasattr(bpy.context,"selected_objects")):
                       previousSelection = bpy.context.selected_objects
                       previousActive = bpy.context.active_object
                   else:
                       previousSelection = []
                   # Now load the new mesh
                   theFileName = stl_files[fileToLoad]
                   newMesh = loadSTL(theFileName,"temporarySTLname")
                   switchMesh(obj,newMesh)
                   if (obj["07 Smooth"] > 0):
                       for face in newMesh.faces:
                           face.use_smooth = True
                   if (obj["08 Color Nodes"] > 0):
                       colorFileNames = obj["09 Color Files"]
                       colorFiles=sorted(glob.glob(os.path.join(pathToSTLFiles, colorFileNames+"*.bin"))) 
                       colorMesh(obj, newMesh ,colorFiles[fileToLoad])
                   # Return selection to previous state
                   if (len(previousSelection)>0):
                       bpy.context.scene.objects.active = previousActive
                       for n in range(len(previousSelection) ):
                           previousSelection[n].select = True                                        

bpy.app.handlers.frame_change_pre.append(onFrameChange)

  """


class ImportSTLSequence(bpy.types.Operator, ImportHelper):
   """Add a STL Sequence object"""
   bl_idname = "import_mesh.stlseq"
   bl_label = "STL Sequence loader"
   bl_description = "Adds a sequence of STL files, one per frame"
   bl_options = {'REGISTER', 'UNDO'}

   filename_ext = ".stl"

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

   def execute(self,context):

       paths = [os.path.join(self.directory, name.name)
                for name in self.files]

       if not paths:
           paths.append(self.filepath)

       if bpy.ops.object.mode_set.poll():
           bpy.ops.object.mode_set(mode='OBJECT')

       if bpy.ops.object.select_all.poll():
           bpy.ops.object.select_all(action='DESELECT')


       # turn off undo for better performance (3-5x faster), also makes sure
       #  that mesh ops are undoable and entire script acts as one operator
#        bpy.context.user_preferences.edit.use_global_undo = False

       # Install the script that will run when the frame change fires.
       try:
           txt = bpy.data.texts["stl_changer.py"]
       except:
           txt = None
       if txt == None:
           # Looks like there is no script for handling the callback so we create it.
           txt = bpy.data.texts.new("stl_changer.py")
           if txt != None:
              txt.clear()
              txt.write(code.__doc__)
              txt.use_module = True
       #Import the code we just created on-the-fly.
       import stl_changer


       for path in paths:
           objName = bpy.path.display_name(os.path.basename(path))

           # Loads the STL file just selected
           objName = "STLSequence"
           mesh = stl_changer.loadSTL(path, objName)

           # Load object into scene
           scene = bpy.context.scene
           loader_obj = bpy.data.objects.new(objName, mesh)
           scene.objects.link(loader_obj)
           loader_obj.select = True   
           # Now we add to the object the properties needed to drive the loading of STLs
           loader_obj["00 Active STL"] = 1
           loader_obj["03 Start Frame"] = bpy.context.scene.frame_start
           loader_obj["04 End Frame"] = bpy.context.scene.frame_end
           loader_obj["06 Loaded Frame"] = -1
           loader_obj["01 Path"] = os.path.dirname(path)
           loader_obj["02 File Names"] = os.path.basename(path).split(".")[0]
           loader_obj["05 Repeat"] = 0
           loader_obj["07 Smooth"] = 0
           loader_obj["08 Color Nodes"]=0
           loader_obj["09 Color Files"] = os.path.basename(path).split(".")[0]
           loader_obj["10 Fix Scale"]=0
           loader_obj["11 Min Value"]=0.0
           loader_obj["12 Max Value"]=1.0
           # Set min/max values
           dict = {"00 Active STL": {"min":0, "max":1}}
           dict["03 Start Frame"]= {"min":1, "max":300000}
           dict["04 End Frame"]=  {"min":1, "max":300000}
           dict["05 Repeat"]=  {"min":0, "max":1}
           dict["07 Smooth"]=  {"min":0, "max":1}
           dict["10 Fix Scale"]= {"min":0, "max":1}
           loader_obj["_RNA_UI"] = dict
           # object generation done

       # Run the loader script once to load into current frame
       stl_changer.onFrameChange(bpy.context.scene)
       # turn undo back on
#        bpy.context.user_preferences.edit.use_global_undo = True 

       return {'FINISHED'}

# Blender boilerplate to incorporate into the UI

def menu_import(self, context):
   self.layout.operator(ImportSTLSequence.bl_idname,
                        text="Stl Sequence(.stl)").filepath = "*.stl"
def register():
   bpy.utils.register_module(__name__)
   bpy.types.INFO_MT_file_import.append(menu_import)

def unregister():
   bpy.utils.unregister_module(__name__)
   bpy.types.INFO_MT_file_import.remove(menu_import)

if __name__ == "__main__":
   register()
