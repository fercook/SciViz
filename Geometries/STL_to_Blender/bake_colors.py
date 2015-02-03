# How this works:
#   In the scene with STL_loader present (or anything that changes the vertex colors in time)
#   Make sure the material of the object is "Shadeless" and that vertex color paint is active
#  Create a UV map -- automatic UV Unwrap works ok, it doesn´t matter really.
#  Create a new image to contain the UV unwrapping you just made.
#  Name your image to something e.g. IMAGENAME
#  Copy the following script into the text editor, 
#  adjust the path where you want the image files
#  adjust the image name
# if your objetcs are in some scene other that the first, change that number too
#  and 
#

import bpy
import stl_changer
import os.path
import sys

#  IF you want to bake textures offline or in batch mode (from the command line)
#  uncomment the following lines and make sure you use the -s (start) and -e (end)
#  options when calling Blender
#  example:
#  blender -b Scene.blend -s 10 -e 34 -P bake.py
#  where bake.py would be THIS script in a file with that name, and the baking would happen 
#  from frames 10 to 34 (inclusive)

iend = sys.argv.index('-e')+1
istart = sys.argv.index('-s')+1
frameend = int(sys.argv[iend])
framestart = int(sys.argv[istart])

ipath = sys.argv.index('-ipath')+1
inputpath= sys.argv[ipath]
opath = sys.argv.index('-opath')+1
outpath= sys.argv[opath]
basename = sys.argv[sys.argv.index('-name')+1]


object=bpy.data.objects['STLSequence']
object["01 Path"] = inputpath
object["04 End Frame"]=frameend

print ("Options read")
print (str(framestart))
print (str(frameend))
print (inputpath)

#
imgname = 'bake'
output_path = outpath
output_basename = basename 
scene = bpy.data.scenes[0]

#These are bake settings
scene.render.use_bake_selected_to_active=True
scene.render.use_bake_antialiasing=True
scene.render.use_bake_clear=True

for frame in range(framestart,frameend+1):
    print (str(frame))
    scene.frame_current = frame
    stl_changer.onFrameChange(scene)
    bpy.ops.object.bake_image()
    filename = os.path.join(output_path, output_basename+"Frame"+str(frame)+".png")
    bpy.data.images[imgname].save_render(filepath=filename)
