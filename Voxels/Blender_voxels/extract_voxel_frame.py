#!/usr/bin/python
#
#  This program extracts a single frame out of multiframe Blender voxel file.
#
#  Syntax:
#
#  extract_single_frame.py filein fileout frame
#
#
import struct;
import math;
import sys;
import array;
from optparse import OptionParser;


usage = "Extract a single frame out of multiframe Blender voxel file. \n
Syntax:    extract_single_frame.py filein fileout frame";
parser = OptionParser(usage=usage);

parser.add_option("-V","--verbose",action="store_true", 
    dest="Verbose",default=False, 
    help="Switch on verbose mode.");
    
# Parse arguments
(options, args) = parser.parse_args();

Verbose = options.Verbose

filenamein = args[0];
filenameout = args[1];
framenumber = args[2];

filein = open(filenamein, "rb")
fileout = open(filenameout, "wb")

headerin = array.array('I')
headerin.fromfile(filein,4)
xres = headerin[0]
yres = headerin[1]
zres = headerin[2]
times = headerin[3]

if (framenumber > times or framenumber < 1):
    print("Incorrect frame, max frame number is "+str(times));
    quit();

headerout = headerin
headerout[3] = 1 # A single frame
headerout.tofile(fileout)

if Verbose:
    print("Out as "+filenameout);
    print("x as "+str(xres));
    print("y as "+str(yres));
    print("z as "+str(zres));

def readframe(file):
    dat = array.array('f');
    dat.fromfile(file, xres*yres*zres)
    return dat;

for t in range (1,framenumber-1):
    if (Verbose):
	print ("Skipping frame "+str(t)+" out of "+str(framenumber-1))
    temporary=readframe(filein);

data=readframe(filein);
data.tofile(fileout)

fileout.flush();
fileout.close();
filein.close();

