Para MinoTauro, usa "launch_mesh_extractor.sh" para lanzar el script extractor de las STL. Me temo que debido a limitaciones de implementación interna de ParaView, sólo se podrá usar en modo secuencial. Como contrapartida funciona bastante bien.

Los archivos "stl_extractor.py" y "stl_sequence.sh" son el script de ParaView y el script de Blender, respectivamente. No los necesitas para MinoTauro, ya los he colocado en producción. En Blender está el script deshabilitado por defecto, así sólo a quién les interese lo cargarán desde el menú de addons. El script se Paraview se usa con el launcher que te he pasado.


Instructions:

You must have a Paraview version with Python scripting support. The precompiled version does have such feature.

Start up Paraview and load the data you want to process.

Prepare the scene completely. The last you should is to apply an "Extract Surface" filter to your data. This is the surface that will be exported.

Save everything in a Paraview State file. (you can quit Paraview after this if you want)

From the command line run:

~$ $PATHTOPARAVIEWBINS/pvpython $PATHTOSCRIPT/stl_extractor.py statefile.pvsm outputpath

