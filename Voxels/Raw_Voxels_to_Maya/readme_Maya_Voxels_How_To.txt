Maya can take several volumetric inputs and connect these inputs to internal variables like density, incandescence, colour, and so on. In Maya's language, the input variables are called channels. They must be interpreted as one of the variables Maya uses for simulating fluids, like temperature, velocity, fuel, but those names are not really meaningful unless you want Maya to control the physics, e.g. you can associate the opacity of the material to the temperature.

Voxels must be put inside Maya's fluid containers. Typically, one has Maya pre-compute the physics of the fluid inside the container and store this pre computation in a cache. What we want to do is to replace this cache by some external data.

For some reason we still don't control, Maya creates fluid containers by default sometimes with 4 and sometimes with 5 channels. If you try to attach a cache with less channels than those, Maya will complain and not do it. Until we find how to create containers with the right number of channels, we have to use a dirty workaround. Later we will learn how to create the external cache files, but for now we need to know the resolution of the data (X, Y, and Z number of voxels), and what type and how many variables we want to convert

1) Open your Maya scene (it can also be a new one).

2) Create a 3D fluid container either from the Fluids tab or from the Fluid Effects menu (in the Dynamics menu set).

3) From the create menu options, or from the Attribute Editor panel, change the resolution of the container to the resolution of your data. From the panel you will need to uncheck the Keep Voxels Square option so you can edit the resolution. Also recommended is to have the size of the box be proportional to the sizes, unless you know what you are doing.

4) In the Attribute editor, go to the Contents Method panel. There you can choose which variables will be animated (from the cache data, but not yet). The five main variables are Density, Velocity, Temperature, Fuel, and Color. Density, Temperature, and Fuel are scalar numbers (one number per voxel), Velocity and Color are vectors (three numbers per voxel). Still they don't mean anything, so whichever you choose is fine as long as the dimensionality of the data is the same. IMPORTANT: If you are not going to use a variable, make sure you set it to Off(zero). You can also work with Gradient and Static Grid options. For the colour, the normal is to Use Shading Color and then map density or some other variable to opacity and a colour ramp.

5) Since we are there, go to the Grids Cache panel in the AE and set to "Read" only those variables that will be read from the cache. This doesn't quite work but it's good to set it to avoid instabilities in Maya.

6) Finally, just so we make this clean, in the AE on top rename the fluid node (it's usually somehitng like fluidShape1 or something). Name it to something you will remember because it will be used later.

7) Here is the dirty part. Go to Fluid nCache menu, and click on the Options of Create New Cache. You will be presented with the most important menu for our purposes:
	7.1) Choose a directory and a cache name. The default directory is fine.
	7.2) For cache format choose mcc, NOT mcx. (This will be lifted in future versions since mcc files can only be 2GB large)
	7.3) Choose One file per frame distribution
	7.4) Time range can be fixed later, so choose something reasonable like 10 frames, but make sure you evaluate and save every 1 frame.
	7.5) The crucial item: Choose ONLY those variables that will be filled later from your cache data. This will somehow reduce the number of channels of the default container (as I said before, 4 or 5) to less (or even more, I haven't tried) depending on how many variables are checked here.
	7.6) Hit Create. This will make a bunch of files in the chosen directory.

8) Go to the Fluid nCache menu and Delete Cache. If you are asked, choose to keep the files on disk. DO NOT DELETE THIS SCENE. Save it or keep it open until you finish.

9) In the file explorer, go to the cache directory. You should see a list of files starting with the cache name you chose in 7.1. One file is an XML file, and the rest are .mc (Maya Cache) files. Delete all the .mc files.

10) Depending on the number of frames you actually have, you should edit or not the XML file. If you need to, in the fourth line or so you will find an item 
  <time Range="250-2500"/>
If you have N frames, change this to
  <time Range="250-N*250"/>
where N*250 is the time of the last frame (multiply those numbers…)
You need to do the same at the end of the file, you will find a description of the end time of all the channels in the cache ( EndTime="2500" ) , change that too.

11) Prepare your input data for the converter script. Each variable that you want to transfer to a channel must be stored in RAW format with x changing fastest, then y and last z. The files must be named with the following convention
basename.VARIABLE.frame
where base name is the same for all channels, VARIABLE is whatever you want (one word), and frame is an integer padded to 5 digits. For example
BigBox.DENSITY.00074

12) Fill in the XML input file for the converter. Here you will describe the resolution of the data, the number of frames, where are the input and output files (as well as their basenames), but very importantly you need to describe the channels that you want to import, wether you want them normalized globally or locally (in each frame), or if you want a logarithmic scale, and so on.
Important: The channelsBaseName that goes here is the one you chose in point 6. However, the outputBaseName must be the cache files name you chose in 7.1.

13) Run the converter
python MayaCacheCreator.py -f input.xml
This will create a list of .mc cache files.

14) Take all those files and put them in the cache directory where Maya expects the fluids cache for the container you created (remember to edit the .xml file for the cache descriptor, step 10)

15) In Maya, select the Fluid container that you prepared before, and go to Fluid nCache, and Attach Existing Cache File. You should be in the cache directory, and select the .xml file you created and maybe modified.

16) Enjoy.


