CONVERT VARIOUS FORMATS TO BINARY

USAGE

HDF5
./hdf5_2_raw.sh VarName X Y Z root

where VarName is the HDF5 variable that you want to export, X Y and Z
are the dimensions of the HDF5 grid (needs to be structured). root is
the root name you want for your output.

 Requires HDF5 utilities installed (in particular h5dump)

NETCDF

ncdump -v var file.nc | netcdf2bin.py [options]

if you ask netcd2bin.py -h you will get help on the options
