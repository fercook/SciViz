#!/usr/bin/python
#
#
#
import struct;
import math;
import sys;
import array;
from optparse import OptionParser;


usage = "Decimate a voxel file in X and Y directions.\n  syntax:  decimate_voxels.py inputfile outputfile [options]";
parser = OptionParser(usage=usage);

parser.add_option("-V","--verbose",action="store_true", 
    dest="Verbose",default=False, 
    help="Switch on verbose mode.");
parser.add_option("-b","--binary",action="store_true", dest="BinaryOriginal",default=False, 
    help="Original file is raw binary.");
parser.add_option("-r","--raw",action="store_true", dest="BinaryOutput",default=False, 
    help="Output file as raw binary.");
parser.add_option("-x",type="int",action="store", dest="Xres",default=32, 
    help="X resolution of binary file.");
parser.add_option("-y",type="int",action="store", dest="Yres",default=32, 
    help="Y resolution of binary file.");
parser.add_option("-z",type="int",action="store", dest="Zres",default=32, 
    help="Z resolution of binary file.");
parser.add_option("-m",type="float",action="store", dest="vMin",default=0.0, 
    help="Minimum value cutoff.");
parser.add_option("-M",type="float",action="store", dest="vMax",default=1.0, 
    help="Maximum value cutoff.");
parser.add_option("-f","--factor",type="int",action="store", dest="Factor",default=2, 
    help="Number of cells to average (default=2).");
    
# Parse arguments
(options, args) = parser.parse_args();

factor = options.Factor;

Verbose = options.Verbose;

BinaryOriginal = options.BinaryOriginal;
BinaryOutput = options.BinaryOutput;

vMin = options.vMin;
vMax = options.vMax;

filenamein = args[0];
filenameout = args[1];

filein = open(filenamein, "rb")
fileout = open(filenameout, "wb")

minim = 1.0E40;
maxim = -1.0E40;

if (BinaryOriginal):
    if Verbose: print "Original binary file"
    xres = options.Xres;
    yres = options.Yres;
    zres = options.Zres;    
    times = 1;
    headerout = array.array('I')
    headerout.append(zres);
    headerout.append(xres/2);
    headerout.append(yres/2);
    headerout.append(times);
else:
    headerin = array.array('I')
    headerin.fromfile(filein,4)
    xres = headerin[0]
    yres = headerin[1]
    zres = headerin[2]
    times = headerin[3]
    headerout = headerin

if not BinaryOutput:
    headerout.tofile(fileout)

if Verbose:
    print("Out as "+filenameout);
    print("x as "+str(xres));
    print("y as "+str(yres));
    print("z as "+str(zres));
    print("T as "+str(times));

for t in range (times):
    if (Verbose):
    	print ("Time "+str(t)+" out of "+str(times))
    data = []
    for x in range(xres):
        if Verbose: print ("Reading col "+str(x)+" out of xres")
        data.append([])
        for y in range(yres):
            col = array.array('f')
            col.fromfile(filein,zres)
            data[x].append(col)
    col = array.array('f')
    for x in range(xres/2):
        if Verbose: print ("Writing col "+str(x)+" out of "+str(xres/2))
        for y in range(yres/2):
            for z in range(zres):
                rtemp = 0.25 * (data[2*x][2*y][z] +data[2*x+1][2*y][z] +data[2*x][2*y+1][z] +data[2*x+1][2+y+1][z]) ;
#                minim = min(minim,rtemp)
#                maxim = max(maxim,rtemp)
                rtemp = min ( max( (rtemp - vMin) / (vMax-vMin) ,0.0) ,1.0);
#                if Verbose: print str(rtemp)
#                rtemp = min ( max(rtemp,0.0) ,1.0)
                col.append( rtemp )            
    col.tofile(fileout)

print "Max: "+str(maxim)
print "Min: "+str(minim)
fileout.flush();
fileout.close();
filein.close();

