from argparse import *
from sys import *
from struct import *
from shutil import *
from math import *
from paraview.simple import *
from paraview.servermanager import *
parser = ArgumentParser(description = 'Process the arguments')
parser.add_argument('binFilePrefix', help = 'Path to the BIN file before the frame index')
parser.add_argument('startFrame', help = 'Min frame number of the sequence')
parser.add_argument('endFrame', help = 'Max frame number of the sequence')
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
    frames.append(args.binFilePrefix + index + '.bin')
# endfor
limitsFile = open(args.binFilePrefix + 'limits.bin', 'rb')
limitsData = limitsFile.read()
limitsArray = unpack_from('f'*(len(limitsData)/calcsize('f') ), limitsData)
globalRange = limitsArray[1] - limitsArray[0]
copy(args.binFilePrefix + 'header.bin', args.binFilePrefix + 'gnorm.bvox')
copy(args.binFilePrefix + 'header.bin', args.binFilePrefix + 'fnorm.bvox')
globalNormFile = open(args.binFilePrefix + 'gnorm.bvox', 'ab')
frameNormFile = open(args.binFilePrefix + 'fnorm.bvox', 'ab')
for i in range(numFrames) :
    frameFile = open(frames[i], 'rb')
    frameData = frameFile.read()
    globalFrameArray = list(unpack_from('f'*(len(frameData)/calcsize('f') ), frameData) )
    frameFrameArray = list(globalFrameArray)
    frameRange = limitsArray[2 * i + 3] - limitsArray[2 * i + 2]
    for j in range(len(globalFrameArray) ) :
        # NORMALIZED_VALUE = (VALUE == nan ? 0.0 : 0.001 + 0.999 * (VALUE - MIN_VALUE) / (MAX_VALUE - MIN_VALUE) )
        if isnan(globalFrameArray[j]) :
          globalFrameArray[j] = 0.0
          frameFrameArray[j] = 0.0
        else :
          if globalRange == 0.0 :
            globalFrameArray[j] = 0.001
          else :
            globalFrameArray[j] = 0.001 + 0.999 * (globalFrameArray[j] - limitsArray[0]) / globalRange
          # endif
          if frameRange == 0.0 :
            frameFrameArray[j] = 0.001
          else :
            frameFrameArray[j] = 0.001 + 0.999 * (frameFrameArray[j] - limitsArray[2 * i + 2]) / frameRange
          # endif
        # endif
    # endfor
    globalNormFile.write(pack('f'*len(globalFrameArray), *globalFrameArray) )
    frameNormFile.write(pack('f'*len(frameFrameArray), *frameFrameArray) )
    frameFile.flush()
    frameFile.close()
# endfor
globalNormFile.flush()
frameNormFile.flush()
globalNormFile.close()
frameNormFile.close()
print 'OK: ' + args.binFilePrefix + 'gnorm.bvox'
print 'OK: ' + args.binFilePrefix + 'fnorm.bvox'
stdout.flush()
