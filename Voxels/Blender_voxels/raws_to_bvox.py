#!/usr/bin/python
#
#  This program converts a series of binary raw files into Blender Voxel format
#
#
import math;
import sys;
import array;
import glob
from optparse import OptionParser;

usage = "Append raw binary files to a single voxel file.\n  syntax:  raws_to_bvox.py inputfile outputfile [options]";
parser = OptionParser(usage=usage);

parser.add_option("-V","--verbose",action="store_true",
    dest="Verbose",default=False,
    help="Switch on verbose mode.");
parser.add_option("-x","--Xresolution",type="int",action="store", dest="xres",default=32,
    help="Resolution in X dimension");
parser.add_option("-y","--Yresolution",type="int",action="store", dest="yres",default=32,
    help="Resolution in X dimension");
parser.add_option("-z","--Zresolution",type="int",action="store", dest="zres",default=32,
    help="Resolution in X dimension");
parser.add_option("-m","--minimum",type="float",action="store", dest="minval",default=0.0,
    help="Minimum value (converted to 0.0)");
parser.add_option("-M","--maximum",type="float",action="store", dest="maxval",default=1.0,
    help="Maximum value (converted to 1.0)");
parser.add_option("-t","--times",type="int",action="store", dest="times",default=100000,
    help="Maximum number of frames to join");
parser.add_option("-n","--normaliza",action="store_true", dest="LocalNormalize",default=False,
    help="Normalize each frame to the local Max/Min");

# Parse arguments
(options, args) = parser.parse_args();

xres = options.xres
yres = options.yres
zres = options.zres
Maximum = options.maxval
Minimum = options.minval
Maxtimes = options.times
Verbose = options.Verbose
LocalNormalize = options.LocalNormalize

if LocalNormalize:
    Maximum=-1.0E40
    Minimum=0.0

filenamein = args[0];
filenameout = args[1];

fileinlist = sorted(glob.glob(filenamein+"*"))
fileout = open(filenameout, "wb")
times = min(Maxtimes,len(fileinlist))

headerout = array.array('I')
headerout.append(zres)
headerout.append(xres)
headerout.append(yres)
headerout.append(times)
headerout.tofile(fileout)

if Verbose:
    print("Out as "+filenameout);
    print("x as "+str(xres));
    print("y as "+str(yres));
    print("z as "+str(zres));
    print("T as "+str(times));
    print("Max is "+str(Maximum));
    print("Min is "+str(Minimum));

def normalize(num):
    return min(1.0,max(0.0,(abs(num)-Minimum)/(Maximum-Minimum)))

for time in range(times):
    filename=fileinlist[time]
    if LocalNormalize:
       with open(filename,"rb") as file:
            if LocalNormalize: Maximum=-1.0E40
            datain=array.array('f')
            if Verbose: print "Reading..."
            for y in range(yres*xres):
                 datain.fromfile(file,zres)
            if Verbose: print "Finding maximum..."
            Maximum=max(Maximum,max(map(abs,datain)))
            if Verbose: print "Max found is "+str(Maximum)
            if (Maximum <= Minimum): Maximum=Minimum+1
            if Verbose: print "Normalizing..."
            dataout=array.array('f',map(normalize, datain))
            if Verbose: 
                print "Writing..."+str(len(dataout))+" numbers"
            dataout.tofile(fileout)
       fileout.flush();
       if Verbose:
            print("Did file "+str(time+1)+" out of "+str(times))
fileout.close();

