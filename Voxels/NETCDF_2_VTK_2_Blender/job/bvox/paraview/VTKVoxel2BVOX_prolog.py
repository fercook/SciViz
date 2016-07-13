from argparse import *
from sys import *
from struct import *
from os.path import *
from paraview.simple import *
from paraview.servermanager import *
parser = ArgumentParser(description = 'Process the arguments')
parser.add_argument('vtkFilePrefix', help = 'Path to the VTK file before the frame index')
parser.add_argument('vtkFileSufix', help = 'Path to the VTK file after the frame index')
parser.add_argument('outputDir', help = 'Path to the output directory (must be writable)')
parser.add_argument('startFrame', help = 'Start frame number of the sequence')
parser.add_argument('endFrame', help = 'End frame number of the sequence')
args = parser.parse_args()
start = -1
end = -1
try :
  start = int(args.startFrame)
except ValueError :
  print >> stderr, 'ERROR: startFrame is not a number. Aborting'
  stderr.flush()
  exit(-1)
# endtry
try :
  end = int(args.endFrame)
except ValueError :
  print >> stderr, 'ERROR: endFrame is not a number. Aborting'
  stderr.flush()
  exit(-2)
# endtry
frames = []
numFrames = end - start + 1
for i in range(numFrames) :
  index = str(start + i).zfill(5)
  frames.append(args.vtkFilePrefix + index + args.vtkFileSufix)
# endfor
if frames != [] :
  vtkReader = OpenDataFile(frames)
  vktInstance = Fetch(vtkReader)
  frameBounds = vktInstance.GetBounds()
  frameExtent = vktInstance.GetExtent()
  res = []
  res.append(frameExtent[1] - frameExtent[0] + 1)
  res.append(frameExtent[3] - frameExtent[2] + 1)
  res.append(frameExtent[5] - frameExtent[4] + 1)
  # Header: XRES, YRES, ZRES, NUMFRAMES
  outputFilePrefix = basename(args.vtkFilePrefix)
  f = open(args.outputDir + '/' + outputFilePrefix + 'header.bin', 'wb')
  f.write(pack('i'*len(res), *res) )
  f.write(pack('i', numFrames) )
  f.flush()
  f.close()
  f = open(args.outputDir + '/' + outputFilePrefix + 'header.txt', 'w')
  f.write('XSIZE: ' + str(frameBounds[1] - frameBounds[0]) + '\n')
  f.write('YSIZE: ' + str(frameBounds[3] - frameBounds[2]) + '\n')
  f.write('ZSIZE: ' + str(frameBounds[5] - frameBounds[4]) + '\n')
  f.write('XRES: ' + str(res[0]) + '\n')
  f.write('YRES: ' + str(res[1]) + '\n')
  f.write('ZRES: ' + str(res[2]) + '\n')
  f.write('NUMFRAMES: ' + str(numFrames) + '\n')
  f.flush()
  f.close()
  programmableFilter1 = ProgrammableFilter(Input=vtkReader)
  programmableFilter1.OutputDataSetType = 'vtkImageData'
  programmableFilter1.Script = '\
import math\n\
executive = self.GetExecutive()\n\
inputImageData = self.GetInput()\n\
inputPointData = inputImageData.GetPointData().GetArray(0)\n\
outInfo = executive.GetOutputInformation(0)\n\
updateExtent = [executive.UPDATE_EXTENT().Get(outInfo, i) for i in range(6)]\n\
imageData = self.GetOutput()\n\
imageData.SetExtent(updateExtent)\n\
imageData.AllocateScalars(vtk.VTK_FLOAT, 1)\n\
pointData = imageData.GetPointData().GetScalars()\n\
pointData.SetName("value")\n\
goodValue = 0.0\n\
dimensions = imageData.GetDimensions()\n\
for i in range(dimensions[0]) :\n\
  for j in range(dimensions[1]) :\n\
    for k in range(dimensions[2]) :\n\
      pointId = vtk.vtkStructuredData.ComputePointId(dimensions, (i, j, k) )\n\
      goodValue = inputPointData.GetValue(pointId)\n\
      if not math.isnan(goodValue) :\n\
        break\n\
    if not math.isnan(goodValue) :\n\
      break\n\
  if not math.isnan(goodValue) :\n\
    break\n\
for i in range(dimensions[0]) :\n\
  for j in range(dimensions[1]) :\n\
    for k in range(dimensions[2]) :\n\
      pointId = vtk.vtkStructuredData.ComputePointId(dimensions, (i, j, k) )\n\
      value = inputPointData.GetValue(pointId)\n\
      if math.isnan(value) :\n\
        pointData.SetValue(pointId, goodValue)\n\
      else :\n\
        pointData.SetValue(pointId, value)'
  programmableFilter1.RequestUpdateExtentScript = ''
  programmableFilter1.CopyArrays = 0
  programmableFilter1.PythonPath = ''
  if 'TimestepValues' in dir(vtkReader) and vtkReader.TimestepValues.__str__() != 'None' and vtkReader.TimestepValues.__len__() != 0:
    limits = [float('+inf'), float('-inf')]
    for timeStep in vtkReader.TimestepValues :
      programmableFilter1.UpdatePipeline(timeStep)
      frameRange = Fetch(programmableFilter1).GetPointData().GetArray(0).GetRange()
      if frameRange[0] < limits[0] :
        limits[0] = frameRange[0]
      # endif
      if frameRange[1] > limits[1] :
        limits[1] = frameRange[1]
      # endif
      limits.append(frameRange[0])
      limits.append(frameRange[1])
    # endfor
    f = open(args.outputDir + '/' + outputFilePrefix + 'limits.bin', 'wb')
    f.write(pack('f'*len(limits), *limits) )
    f.flush()
    f.close()
    f = open(args.outputDir + '/' + outputFilePrefix + 'limits.txt', 'w')
    f.write('GLOBAL MIN: ' + str(limits[0]) + '\n')
    f.write('GLOBAL MAX: ' + str(limits[1]) + '\n')
    for i in range(numFrames) :
      f.write('FRAME ' + str(i) + ' MIN: ' + str(limits[2 * i + 2]) + '\n')
      f.write('FRAME ' + str(i) + ' MAX: ' + str(limits[2 * i + 3]) + '\n')
    # endfor
    f.flush()
    f.close()
  else :
    programmableFilter1.UpdatePipeline()
    frameRange = Fetch(programmableFilter1).GetPointData().GetArray(0).GetRange()
    f = open(args.outputDir + '/' + outputFilePrefix + 'limits.bin', 'wb')
    f.write(pack('f'*len(frameRange), *frameRange) )
    f.flush()
    f.close()
    f = open(args.outputDir + '/' + outputFilePrefix + 'limits.txt', 'w')
    f.write("MIN: " + str(frameRange[0]) + "\n")
    f.write("MAX: " + str(frameRange[1]) + "\n")
    f.flush()
    f.close()
  # endif
# endif
