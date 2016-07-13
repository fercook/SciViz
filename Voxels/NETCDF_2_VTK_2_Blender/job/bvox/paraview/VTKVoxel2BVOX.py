from argparse import *
from sys import *
from os.path import *
from paraview.simple import *
from paraview.servermanager import *
parser = ArgumentParser(description = 'Process the arguments')
parser.add_argument('vtkFile', help = 'Path to the VTK file')
parser.add_argument('outputDir', help = 'Path to the output directory (must be writable)')
args = parser.parse_args()
vtkReader = OpenDataFile(args.vtkFile)
frameData = Fetch(vtkReader).GetPointData().GetArray(0)
outputFilePrefix = splitext(basename(args.vtkFile) )[0]
f = open(args.outputDir + '/' + outputFilePrefix + '.bin', 'wb')
f.write(frameData)
f.flush()
f.close()
