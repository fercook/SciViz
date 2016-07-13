from argparse import *
from sys import *
from os.path import *
from vtk import *
from paraview.simple import *
from paraview.servermanager import *
parser = ArgumentParser(description = 'Process the arguments')
parser.add_argument('vtkFile', help = 'Path to the VTK file')
parser.add_argument('outputDir', help = 'Path to the output directory (must be writable)')
args = parser.parse_args()
vtkReader = OpenDataFile(args.vtkFile)
frameInstance = Fetch(vtkReader)
frameRange = frameInstance.GetPointData().GetArray(0).GetRange()
vtkImgCast = vtkImageShiftScale()
vtkImgCast.SetShift(-frameRange[0])
vtkImgCast.SetScale(1.0 / (frameRange[1] - frameRange[0]) )
vtkImgCast.SetOutputScalarTypeToFloat()
vtkImgCast.SetInputData(frameInstance)
vtkImgCast.Update()
vtkImgWriter = vtkTIFFWriter()
vtkImgWriter.SetCompressionToNoCompression()
outputFilePrefix = splitext(basename(args.vtkFile) )[0]
fileName = args.outputDir + '/' + outputFilePrefix + '.tiff'
vtkImgWriter.SetFileName(fileName)
vtkImgWriter.SetInputConnection(vtkImgCast.GetOutputPort() )
vtkImgWriter.Write()
print 'OK: ' + fileName
stdout.flush()
