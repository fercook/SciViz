import options
import array

usage = "Convert Gaussian Cube file format to a raw binary file. \n It also outputs header information needed to interpret the raw file.\n  syntax:  gcubetoraw.py inputfile outputfile headeroutputfile";

SiestaFileName = args[0]
RawFileName = args[1]
HeaderFileName = args[2]

filein = open(SiestaFileName,'r')
header = open(HeaderFileName,'w')

#Header information
line=filein.readline()
line.tofile(header)
line=filein.readline()
line.tofile(header)

#Number of atoms
line = filein.readline()
line.tofile(header)
splitLine = line.split()
NumAtoms = int(splitLine[0])
Origin = map( float,splitLine[1:3])
#Voxel resolution
Resolution = [1,1,1]
BoxAxes = [[],[],[]]
for dim in range(3):
    line = filein.readline()
    line.tofile(header)
    splitLine = line.split()
    Resolution[dim]=int(splitLine[0])
    BoxAxes[dim]=map( float, splitLine[1:3])
#Read atom positions
Atoms = []
for atom in range(NumAtoms):
    line = filein.readline()
    line.tofile(header)
    splitLine = line.split()
    Atoms.append( [int(splitLine[0]),  map( float, splitLine[2:4]) )
filein.close()
header.close()

#Now output the raw binary
NumVoxels = Resolution[0]*Resolution[1]*Resolution[2]
voxeldata = array.array('f')
for line in filein:
    splitLine = line.split()
    for num in map(float, splitline):
        voxeldata.append(num)

if (len(voxeldata) != NumVoxels):
    print ("Wrong number of voxel data read. Expected "+str(NumVoxels)+", found "+str(len(voxeldata)))
    exit()
    
fileout = open(RawFileName, 'wb')
voxeldata.tofile(fileout)
fileout.close()
