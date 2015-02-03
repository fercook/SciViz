#!/usr/bin/python
#
#  This program converts a variable in NetCDF format to Blender voxels
#  It requires the program ncdump to export a single variable into ASCII CSV format, 
#  and the program uses the unix pipeline to avoid creating large temporary files. 
#  Make sure you have ncdump in your path.
#
#  Syntax:
#
#  ncdump -v variable NetCDFfile.nc  |  voxels_from_NetCDF.py
#
#  where variable is what you want to export to Blender voxels
#
#
import struct;
import math;
import sys;
import array;
from optparse import OptionParser;


usage = "Increase the total number of voxel data by creating linearly interpolated frames between existing ones.\n  syntax:  doublevoxels.py inputfile outputfile [options]";
parser = OptionParser(usage=usage);

parser.add_option("-V","--verbose",action="store_true", 
    dest="Verbose",default=False, 
    help="Switch on verbose mode.");
parser.add_option("-x","--xfactor",type="int",action="store", dest="Factor",default=2, 
    help="Time factor to increase the data (default=2).");
    
# Parse arguments
(options, args) = parser.parse_args();

factor = options.Factor

Verbose = options.Verbose

filenamein = args[0];
filenameout = args[1];

filein = open(filenamein, "rb")
fileout = open(filenameout, "wb")

headerin = array.array('I')
headerin.fromfile(filein,4)
xres = headerin[0]
yres = headerin[1]
zres = headerin[2]
times = headerin[3]

headerout = headerin
newtimes = headerout[3] = factor * headerout[3] - 1

headerout.tofile(fileout)

if Verbose:
    print("Out as "+filenameout);
    print("x as "+str(xres));
    print("y as "+str(yres));
    print("z as "+str(zres));
    print("T as "+str(times));

def tofile(dat,file):
    for x in range(xres):
	for y in range(yres):
	    dat[x][y].tofile(file)

datanow = []
for x in range(xres):
    datanow.append([])
    for y in range(yres):
	col = array.array('f')
	col.fromfile(filein,zres)
	datanow[x].append(col)
tofile( datanow, fileout)

for t in range (times-1):
    if (Verbose):
	print ("Time "+str(t)+" out of "+str(times))
    datafuture = []
    for x in range(xres):
	datafuture.append([])
	for y in range(yres):
	    col = array.array('f')
	    col.fromfile(filein,zres)
	    datafuture[x].append(col)
    for x in range(xres):
	for y in range(yres):
	    for z in range(zres):
		datanow[x][y][z] = (datanow[x][y][z]+datafuture[x][y][z])/factor
    tofile( datanow, fileout)
    tofile( datafuture, fileout)
    datanow = datafuture

fileout.flush();
fileout.close();
filein.close();

