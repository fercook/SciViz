from argparse import *
from sys import *
from os.path import *
from paraview.simple import *
from paraview.servermanager import *
parser = ArgumentParser(description = 'Process the arguments')
parser.add_argument('inputFile', help = 'Path to the input file (NetCDF compilant)')
parser.add_argument('outputDir', help = 'Path to the output directory (must be writable)')
parser.add_argument('fieldName', help = 'The field to be extracted')
parser.add_argument('dimensions', help = 'Dimension of the fieldName, with the pattern: (dim1, dim2, ..., dimN)')
parser.add_argument('massage', help = 'Equation to be applied to the field to obtain a linear value')
parser.add_argument('xFactor', help = 'X Grid factor applied to the X extent')
parser.add_argument('yFactor', help = 'Y Grid factor applied to the Y extent')
parser.add_argument('zFactor', help = 'Z Grid factor applied to the Z extent')
args = parser.parse_args()
xFactor = -1.0
yFactor = -1.0
zFactor = -1.0
try :
    xFactor = float(args.xFactor)
except ValueError :
    print >> stderr, 'ERROR: xFactor is not a number. Aborting'
    stderr.flush()
    exit(-3)
# endtry
if xFactor < 0.0 :
    print >> stderr, 'ERROR: xFactor is not a positive number. Aborting'
    stderr.flush()
    exit(-4)
# endif
try :
    yFactor = float(args.yFactor)
except ValueError :
    print >> stderr, 'ERROR: yFactor is not a number. Aborting'
    stderr.flush()
    exit(-5)
# endtry
if yFactor < 0.0 :
    print >> stderr, 'ERROR: yFactor is not a positive number. Aborting'
    stderr.flush()
    exit(-6)
# endif
try :
    zFactor = float(args.zFactor)
except ValueError :
    print >> stderr, 'ERROR: zFactor is not a number. Aborting'
    stderr.flush()
    exit(-7)
# endtry
if zFactor < 0.0 :
    print >> stderr, 'ERROR: zFactor is not a positive number. Aborting'
    stderr.flush()
    exit(-8)
# endif
netCDFReader1 = NetCDFReader(FileName=[args.inputFile])
netCDFReader1.Dimensions = args.dimensions
netCDFReader1.SphericalCoordinates = 0
netCDFReader1.VerticalScale = 1.0
netCDFReader1.VerticalBias = 0.0
netCDFReader1.ReplaceFillValueWithNan = 1
netCDFReader1.OutputType = 'Image'
scene = GetAnimationScene()
scene.Caching = 0
steps = scene.TimeKeeper.TimestepValues
if 0 < steps.__str__() != 'None' and steps.__len__() != 0 :
  scene.AnimationTime = steps[0]
# endif
netCDFReader1.UpdatePipeline(scene.AnimationTime)
passArrays1 = PassArrays(Input=netCDFReader1)
passArrays1.PointDataArrays = [args.fieldName]
passArrays1.CellDataArrays = []
passArrays1.FieldDataArrays = []
passArrays1.UpdatePipeline()
programmableSource1 = ProgrammableSource()
programmableSource1.OutputDataSetType = 'vtkImageData'
programmableSource1.Script = '\
executive = self.GetExecutive()\n\
outInfo = executive.GetOutputInformation(0)\n\
updateExtent = [executive.UPDATE_EXTENT().Get(outInfo, i) for i in range(6)]\n\
imageData = self.GetOutput()\n\
imageData.SetExtent(updateExtent)\n\
imageData.AllocateScalars(vtk.VTK_FLOAT, 1)\n\
pointData = imageData.GetPointData().GetScalars()\n\
pointData.SetName("' + args.fieldName + '")\n\
dimensions = imageData.GetDimensions()\n\
for i in range(dimensions[0]) :\n\
  for j in range(dimensions[1]) :\n\
    for k in range(dimensions[2]) :\n\
      pointId = vtk.vtkStructuredData.ComputePointId(dimensions, (i, j, k) )\n\
      pointData.SetValue(pointId, 0.0)'
programmableSource1.ScriptRequestInformation = '\
import paraview.simple\n\
import math\n\
executive = self.GetExecutive()\n\
outInfo = executive.GetOutputInformation(0)\n\
source = paraview.simple.FindSource("NetCDFReader1")\n\
extent = source.GetDataInformation().GetExtent()\n\
bounds = source.GetDataInformation().GetBounds()\n\
xExtent = ' + str(xFactor) + ' * (extent[1] - extent[0])\n\
xSpacing = bounds[1] - bounds[0]\n\
if xExtent != 0.0 :\n\
  xFactor = math.ceil(xExtent) * ' + str(xFactor) + ' / xExtent\n\
  xExtent = int(round(xFactor *(extent[1] - extent[0]) ) )\n\
  xSpacing = xSpacing / xExtent\n\
else :\n\
  xExtent = int(xExtent)\n\
yExtent = ' + str(yFactor) + ' * (extent[3] - extent[2])\n\
ySpacing = bounds[3] - bounds[2]\n\
if yExtent != 0.0 :\n\
  yFactor = math.ceil(yExtent) * ' + str(yFactor) + ' / yExtent\n\
  yExtent = int(round(yFactor * (extent[3] - extent[2]) ) )\n\
  ySpacing = ySpacing / yExtent\n\
else :\n\
  yExtent = int(yExtent)\n\
zExtent = ' + str(zFactor) + ' * (extent[5] - extent[4])\n\
zSpacing = bounds[5] - bounds[4]\n\
if zExtent != 0.0 :\n\
  zFactor = math.ceil(zExtent) * ' + str(zFactor) + ' / zExtent\n\
  zExtent = int(round(zFactor * (extent[5] - extent[4]) ) )\n\
  zSpacing = zSpacing / zExtent\n\
else :\n\
  zExtent = int(zExtent)\n\
outInfo.Set(executive.WHOLE_EXTENT(), 0, xExtent, 0, yExtent, 0, zExtent)\n\
outInfo.Set(vtk.vtkDataObject.ORIGIN(), bounds[0], bounds[2], bounds[4])\n\
outInfo.Set(vtk.vtkDataObject.SPACING(), xSpacing, ySpacing, zSpacing)\n\
dataType = 10\n\
numberOfComponents = 1\n\
vtk.vtkDataObject.SetPointDataActiveScalarInfo(outInfo, dataType, numberOfComponents)'
programmableSource1.PythonPath = ''
programmableSource1.UpdatePipeline()
resampleWithDataset1 = ResampleWithDataset(Input=passArrays1, Source=programmableSource1)
resampleWithDataset1.PassCellArrays = 0
resampleWithDataset1.PassPointArrays = 0
resampleWithDataset1.PassFieldArrays = 1
resampleWithDataset1.ComputeTolerance = 1
resampleWithDataset1.UpdatePipeline()
programmableFilter1 = ProgrammableFilter(Input=resampleWithDataset1)
programmableFilter1.OutputDataSetType = 'vtkImageData'
programmableFilter1.Script = '\
executive = self.GetExecutive()\n\
inputImageData = self.GetInput()\n\
inputPointData = inputImageData.GetPointData().GetArray(0)\n\
inputMaskPointData = inputImageData.GetPointData().GetArray(1)\n\
outInfo = executive.GetOutputInformation(0)\n\
updateExtent = [executive.UPDATE_EXTENT().Get(outInfo, i) for i in range(6)]\n\
imageData = self.GetOutput()\n\
imageData.SetExtent(updateExtent)\n\
imageData.AllocateScalars(vtk.VTK_FLOAT, 1)\n\
pointData = imageData.GetPointData().GetScalars()\n\
pointData.SetName("' + args.fieldName + '")\n\
dimensions = imageData.GetDimensions()\n\
for i in range(dimensions[0]) :\n\
  for j in range(dimensions[1]) :\n\
    for k in range(dimensions[2]) :\n\
      pointId = vtk.vtkStructuredData.ComputePointId(dimensions, (i, j, k) )\n\
      if inputMaskPointData.GetValue(pointId) != "" :\n\
        DEM=inputPointData.GetValue(pointId)\n\
        pointData.SetValue(pointId, ' + args.massage + ')\n\
      else :\n\
        pointData.SetValue(pointId, float("nan") )'
programmableFilter1.RequestInformationScript = '\
import paraview.simple\n\
import math\n\
executive = self.GetExecutive()\n\
outInfo = executive.GetOutputInformation(0)\n\
source = paraview.simple.FindSource("NetCDFReader1")\n\
extent = source.GetDataInformation().GetExtent()\n\
bounds = source.GetDataInformation().GetBounds()\n\
xExtent = ' + str(xFactor) + ' * (extent[1] - extent[0])\n\
xSpacing = bounds[1] - bounds[0]\n\
if xExtent != 0.0 :\n\
  xFactor = math.ceil(xExtent) * ' + str(xFactor) + ' / xExtent\n\
  xExtent = int(round(xFactor *(extent[1] - extent[0]) ) )\n\
  xSpacing = xSpacing / xExtent\n\
else :\n\
  xExtent = int(xExtent)\n\
yExtent = ' + str(yFactor) + ' * (extent[3] - extent[2])\n\
ySpacing = bounds[3] - bounds[2]\n\
if yExtent != 0.0 :\n\
  yFactor = math.ceil(yExtent) * ' + str(yFactor) + ' / yExtent\n\
  yExtent = int(round(yFactor * (extent[3] - extent[2]) ) )\n\
  ySpacing = ySpacing / yExtent\n\
else :\n\
  yExtent = int(yExtent)\n\
zExtent = ' + str(zFactor) + ' * (extent[5] - extent[4])\n\
zSpacing = bounds[5] - bounds[4]\n\
if zExtent != 0.0 :\n\
  zFactor = math.ceil(zExtent) * ' + str(zFactor) + ' / zExtent\n\
  zExtent = int(round(zFactor * (extent[5] - extent[4]) ) )\n\
  zSpacing = zSpacing / zExtent\n\
else :\n\
  zExtent = int(zExtent)\n\
outInfo.Set(executive.WHOLE_EXTENT(), 0, xExtent, 0, yExtent, 0, zExtent)\n\
outInfo.Set(vtk.vtkDataObject.ORIGIN(), bounds[0], bounds[2], bounds[4])\n\
outInfo.Set(vtk.vtkDataObject.SPACING(), xSpacing, ySpacing, zSpacing)\n\
dataType = 10\n\
numberOfComponents = 1\n\
vtk.vtkDataObject.SetPointDataActiveScalarInfo(outInfo, dataType, numberOfComponents)'
programmableFilter1.RequestUpdateExtentScript = ''
programmableFilter1.CopyArrays = 0
programmableFilter1.PythonPath = ''
programmableFilter1.UpdatePipeline()
dataInfo = programmableFilter1.PointData[args.fieldName]
outputFileName = splitext(basename(args.inputFile) )[0] + '_' + args.fieldName
if dataInfo != None :
  writer = DataSetWriter(FileName=args.outputDir + '/' + outputFileName + '.vtk', FileType=2, Input=programmableFilter1, Writealltimestepsasfileseries=0)
  writer.UpdatePipeline()
  print 'OK: [DEM, FD:' + args.fieldName + ', DIM:' + args.dimensions + ']: ' + outputFileName
  stdout.flush()
  exit(0)
# endif
print >> stderr, 'KO: [DEM, FD:' + args.fieldName + ', DIM:' + args.dimensions + ']: ' + outputFileName
stderr.flush()
exit(1)
