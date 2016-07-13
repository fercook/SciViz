#-
# ==========================================================================
# Copyright 1995,2006,2008 Autodesk, Inc. All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk
# license agreement provided at the time of installation or download,
# or which otherwise accompanies this software in either electronic
# or hard copy form.
# ==========================================================================
#+

import os
import os.path
import getopt
import sys
from xml.etree import cElementTree
import re
import array
import glob
import math

Debug = False

"""
File names
==========

Binary files must be named in the following way

BaseName.CHANNEL.frame
# Read info from input file
inputXMLFileName = ""
outputBaseName = "lleno"
channelsBaseName = "fluidShape1"
inputBaseName = "color"
numFrames = 24
resolution = [3,4,5]
boxSize = [3,4,5]
# CHANNEL, MayaChannelName
channelNames = {}
channelNames['DENSITY']=channelsBaseName+'_density'
channelNames['TEMPERATURE']=channelsBaseName+'_temperature'

Input file format (XML)
======================

<MayaCache name="NameOfCacheInMaya">

<properties>
  <frames>100</frames>
  <size> 2.0, 2.0, 3.0 </size>
  <type> Particles|Fluids </type>
  <resolution> x, y z </resolution> (for Fluids)
  <offset> 0,0,0 </offset>    (for Fluids)
  <normalization>  On|Off|Global|Local </normalization>
</properties>

<files>
  <input>
    <path> /the/path/to/binary/input </path>
    <basename> InputRAWBaseName </basename>
  </input>
  <output>
    <path> /the/path/to/binary/output </path>
    <basename> OutputFilesBaseName </basename>
  </output>
  <cacheXML>
    <path> /the/path/to/cache/xml </path>
    <basename> MayaCacheXMLFileName </basename>
  </cacheXML>
</files>

<channels>
  <channel name="SomeName">
    <interpretation> density </interpretation>
    <mayatype> FBCA </mayatype>
    <source type="File">CHANNELEXTENSION</source>
    <normalization> Off|Global|Local </normalization>
    <scale> Normal | Logarithmic </scale>
  </channel>
  <channel name="OtherName">
    <interpretation> temperature </interpretation>
    <mayatype> FVCA </mayatype>
    <source type="Array"> 11.0, 12.3, 6.4  </source>
    <normalization> Off|Global|Local </normalization>
    <scale> Normal | Logarithmic </scale>
  </channel>
</channels>

</MayaCache>


=================================
From Maya's documentation:
=================================


Overview of Maya Caches:
========================

Conceptually, a Maya cache consists of 1 or more channels of data.
Each channel has a number of properties, such as:

- start/end time
- data type of the channel (eg. "DoubleVectorArray" to represents a point array)
- interpretation (eg. "positions" the vector array represents position data, as opposed to per vertex normals, for example)
- sampling type (eg. "regular" or "irregular")
- sampling rate (meaningful only if sampling type is "regular")

Each channel has a number of data points in time, not necessarily regularly spaced,
and not necessarily co-incident in time with data in other channels.
At the highest level, a Maya cache is simply made up of channels and their data in time.

On disk, the Maya cache is made up of a XML description file, and 1 or more data files.
The description file provides a high level overview of what the cache contains,
such as the cache type (one file, or one file per frame), channel names, interpretation, etc.
The data files contain the actual data for the channels.
In the case of one file per frame, a naming convention is used so the cache can check its
available data at runtime.

Here is a visualization of the data format of the OneFile case:

//  |---CACH (Group)    // Header
//  |     |---VRSN        // Version Number (char*)
//  |     |---STIM        // Start Time of the Cache File (int)
//  |     |---ETIM        // End Time of the Cache File (int)
//  |
//  |---MYCH (Group)    // 1st Time
//  |     |---TIME        // Time (int)
//  |     |---CHNM        // 1st Channel Name (char*)
//  |     |---SIZE        // 1st Channel Size
//  |     |---DVCA        // 1st Channel Data (Double Vector Array)
//  |     |---CHNM        // n-th Channel Name
//  |     |---SIZE        // n-th Channel Size
//  |     |---DVCA        // n-th Channel Data (Double Vector Array)
//  |     |..
//  |
//  |---MYCH (Group)    // 2nd Time
//  |     |---TIME        // Time
//  |     |---CHNM        // 1st Channel Name
//  |     |---SIZE        // 1st Channel Size
//  |     |---DVCA        // 1st Channel Data (Double Vector Array)
//  |     |---CHNM        // n-th Channel Name
//  |     |---SIZE        // n-th Channel Size
//  |     |---DVCA        // n-th Channel Data (Double Vector Array)
//  |     |..
//  |
//  |---..
//    |
//

In a multiple file caches, the only difference is that after the
header "CACH" group, there is only one MYCH group and there is no
TIME chunk.    In the case of one file per frame, the time is part of
the file name - allowing Maya to scan at run time to see what data
is actually available, and it allows users to move data in time by
manipulating the file name.

!Note that it's not necessary to have data for every channel at every time.

"""

#Global variable don't mess with me

Verbose = True

platform = sys.platform
needSwap = False
#This code does not work...
if re.compile("win").match(platform) != None :
    needSwap = True
if re.compile("linux").match(platform) != None :
    needSwap = True
# So I need to swap bytes because I always work on Intel arch.
needSwap = True

def fileFormatError():
    print "Error: unable to read cache format\n";
    sys.exit(2)

def readInt(fd):
    intArray = array.array('i')
    intArray.fromfile(fd,1)
    if needSwap:
        intArray.byteswap()
    return intArray[0]

def writeInt(theInt,fd):
    intArray = array.array('i')
    intArray.append(theInt)
    if needSwap:
        intArray.byteswap()
    intArray.tofile(fd)

def writeFloat(theFloat,fd):
    floatArray = array.array('f')
    floatArray.append(theFloat)
    if needSwap:
        floatArray.byteswap()
    floatArray.tofile(fd)

def writeFloatArray(theFloatArray,fd):
    if needSwap:
        theFloatArray.byteswap()
    theFloatArray.tofile(fd)

    # BASE CLASS
class CacheChannel:
    name = ""
    type = ""
    typeLength = 0
    arrayLength = 0
    normalization = None
    scale = None
    source = ""
    def __init__(self,channelName,channelType,arrayLength,source,normalization=None,scale=None):
        self.name = channelName
        self.type = channelType
        self.arrayLength = arrayLength
        self.source = source
        self.maxBufferLength = 4000000
        self.normalization = normalization
        self.scale = scale
        if channelType == "FVCA":
            #FVCA == Float Vector Array 3 * 4
            self.typeLength = 3*4
        elif channelType == "DVCA":
            #DVCA == Double Vector Array 8 * 3
            self.typeLength = 3*8
        elif channelType == "DBLA":
            #DBLA == Double Array 8
            self.typeLength = 8
        elif channelType == "FBCA":
            #FBCA == Float Array 4
            self.typeLength = 4

    def writeToFile(self,outFile):
        if self.type == "DVCA" or  self.type == "DBLA":
            print "Double arrays not supported yet"
            exit()
        if (Debug):
          print("Trying to write "+self.name+" channel")
        # TAG: Channel name
        outFile.write("CHNM")                     # 4 bytes
                                                  # How many bytes for channel name
        chnmSize = len(self.name)
        writeInt(chnmSize+1,outFile)       # For some reason the size is written as +1
                                         # Channel name
        outFile.write(self.name)           # name bytes
                                           # We need to pad to multiple of 4 bytes
                                           #The string is padded out to 32 bit boundaries,
                                           #so we may need to write more than chnmSize
        mask = 3
        chnmSizeToWrite = (chnmSize + mask) & (~mask)
        if (chnmSizeToWrite == chnmSize): chnmSizeToWrite += 4
        paddingSize = chnmSizeToWrite-chnmSize
        if paddingSize > 0:
            Zero=array.array('b')
            Zero.append(0)
            for n in range(paddingSize):
                Zero.tofile(outFile)
                # TAG: Length of array
        outFile.write("SIZE")                     # 4 bytes
                                             # How many bytes for Length of array
        numBytes = 4
        writeInt(numBytes,outFile)       # 4 bytes
                                         # Length of array in the channel
        arrayLength = self.arrayLength
        writeInt(arrayLength,outFile)    # 4 bytes
                                         # TAG: Type of array
        outFile.write(self.type)           # 4 bytes
                                           # Buffer length
        bufferLength = self.arrayLength * self.typeLength
        writeInt(bufferLength,outFile)    # 4 bytes

        # And now write the actual channel data, subclass dependent
        self.writeDataToFile(outFile,bufferLength)

    def writeDataToFile(self,outFile,bufferLength):
      repetitions = bufferLength/(4*len(self.source))
      mydataout=array.array('f',self.source)
      if needSwap:
         mydataout.byteswap()
      for rep in range(repetitions):
        mydataout.tofile(outFile)

    def getBlockSize(self):
            blockSize = 4 # CHMN
            blockSize += 4 # Channel name size
            chnmSize = len(self.name)
            mask = 3
            chnmSizeToWrite = (chnmSize + mask) & (~mask)
            if (chnmSizeToWrite == chnmSize): chnmSizeToWrite += 4
            blockSize += chnmSizeToWrite # Padded length of channel name
            blockSize += 4 # SIZE
            blockSize += 4 # Size of length of array
            blockSize += 4 # Length of array
            blockSize += 4 # Type of array
            blockSize += 4 # Buffer length
            arrayLength = self.arrayLength
            bufferSize = arrayLength * self.typeLength
            blockSize += bufferSize
            print ("Returning channel "+self.name+" size "+str(blockSize))
            return blockSize


class CacheChannelFromFile(CacheChannel):
    def writeDataToFile(self,outFile,bufferLength):
        # And now write the actual channel data
        if self.normalization == "Local":
            inFile = open(self.source,"rb")
            datain = array.array('f')
            minim = min(datain)
            maxim = max(datain)
            self.normalization = [minim,maxim]
            inFile.close()
            datain = array.array('f')
        inFile = open(self.source,"rb")
        bytesRead = 0
        while bytesRead < bufferLength:
            datain = array.array('f')
            byteChunk = min(self.maxBufferLength, bufferLength-bytesRead)/4
            if (Debug): print ("Read "+str(bytesRead)+", reading "+str(byteChunk))
            datain.fromfile(inFile,byteChunk)
            if self.normalization != None:
                Minimum=self.normalization[0]
                Maximum=self.normalization[1]
                if self.scale == "Logarithmic":
                    def normalize(num):
                        return min(1.0,max(0.0,(math.log(num)-math.log(Minimum))/(math.log(Maximum)-math.log(Minimum))))
                else:
                    def normalize(num):
                        return min(1.0,max(0.0,(num-Minimum)/(Maximum-Minimum)))
                if Verbose: print "Normalizing to "+str(Minimum)+", "+str(Maximum)
                dataout = array.array('f',map(normalize,datain))
            else:
                dataout=datain
            if needSwap:
              dataout.byteswap()
            dataout.tofile(outFile)
            bytesRead += byteChunk*4
        inFile.close()

class CacheFile:
    cacheStartTime = 0
    cacheEndTime = 0
    channels = []

    ########################################################################
    #   Description:
    #       Class constructor - tries to figure out how many input files
    #       are there before construction of the channels
    #       Actual construction of the data files is left for another method
    #
    def __init__(self,cacheStartTime,cacheEndTime,channels):

        self.cacheStartTime = cacheStartTime
        self.cacheEndTime = cacheStartTime
        self.channels = channels

    ########################################################################
    # Description:
    #   method to write the contents of the data file, for the
    #   file per frame case ("OneFilePerFrame")
    def writeDataFilePerFrame(self,fileName):

        if Verbose:
            print "--------------------------------------------------------------\n"
            print "Writing cache data file: "+fileName

        fd = open(fileName,"wb")

        # TAG: Initial tag is FOR4, indicating 4 byte numbers(this is for less than 2GB files)
        fd.write("FOR4")
        #Next comes number of bytes in header. For now it's always 40
        headerSize = 40
        writeInt(headerSize,fd)
        # TAG: This is a cache file
        fd.write("CACH")
        # TAG: Version of cache
        fd.write("VRSN")
        # How many bytes for version
        numBytes = 4
        writeInt(numBytes,fd)
        # The version
        fd.write("0.1 ")
        # TAG: Start time
        fd.write("STIM")
        # How many bytes fortime
        numBytes = 4
        writeInt(numBytes,fd)
        # Initial time ///////////CHECK OUT
        numBytes = self.cacheStartTime
        writeInt(numBytes,fd)
        # TAG: END time
        fd.write("ETIM")
        # How many bytes fortime
        numBytes = 4
        writeInt(numBytes,fd)
        # End time ///////////CHECK OUT
        numBytes = self.cacheEndTime
        writeInt(numBytes,fd)
        # END MAIN HEADER

        # START CHANNEL HEADERS
        # TAG: Initial tag is always FOR4 or FOR8
        fd.write("FOR4")
        #Next comes number of bytes in this block
        blockSize = 4 #MYCH Header
        for dataChannel in self.channels:
            blockSize += dataChannel.getBlockSize()
        writeInt(blockSize,fd)

        # TAG: Next is all channel information
        fd.write("MYCH")
        for dataChannel in self.channels:
            #            if Verbose:
                #                print "Saving channel "+dataChannel.name
            dataChannel.writeToFile(fd)
            #
        # Close all and go home
        fd.close()
        if Verbose:
            print "All  channels saved\n"
            print "--------------------------------------------------------------\n"

            # ************************************************************
            # ************************************************************
            # ************************************************************
            # ************************************************************
            # ************************************************************
            #
def usage():
    print "script -f input.xml \n"

try:
    (opts, args) = getopt.getopt(sys.argv[1:], "f:")
except getopt.error:
    # print help information and exit:
    usage()
    sys.exit(2)

if len(opts) == 0:
    usage()
    sys.exit(2)

# Read info from input file
inputXMLFileName = ""
for o,a in opts:
    if o == "-f":
        inputXMLFileName = a

xmlTree = cElementTree.parse(inputXMLFileName)
xmlRoot = xmlTree.getroot()

#General properties
xmlProperties = xmlRoot.find('properties')
numFrames = int(xmlProperties.find('frames').text)
cacheType = xmlProperties.find('type').text.strip().title()

if (cacheType == "Fluids"):
  resolution = map ( int , xmlProperties.find('resolution').text.split(',') )
  boxSize = map ( float , xmlProperties.find('size').text.split(',') )
  offset = map ( float , xmlProperties.find('offset').text.split(',') )
else:
  numberofparticles = int (xmlProperties.find('type').attrib['number'].strip())

Normalization = xmlProperties.find('normalization').text.strip().title()
if Normalization == "Off":
    Normalization = None

#input output file names
xmlFiles = xmlRoot.find('files')
outputBaseName = xmlFiles.find('output').find('basename').text.strip()
outputpath = xmlFiles.find('output').find('path').text.strip()
inputBaseName = xmlFiles.find('input').find('basename').text.strip()
inputPath = xmlFiles.find('input').find('path').text.strip()
mayaXMLFile = xmlFiles.find('cacheXML').find('basename').text.strip()

#Channel information
xmlChannels = xmlRoot.find('channels')
channelNames = {}
channelSizes = {}
channelTypes = {}
channelNormalization = {}
channelScale = {}
channelSources = {}
channelsBaseName = xmlRoot.attrib['name'].strip()
for xmlChannel in xmlChannels:
    base = xmlChannel.attrib['name'].strip()
    print "Found channel " + base
    channelNames[base] = channelsBaseName+'_'+xmlChannel.find('interpretation').text.strip()
    channelTypes[base] = xmlChannel.find('mayatype').text.strip()
    channelNormalization[base] = xmlChannel.find('normalization').text.strip().title()
    if( channelNormalization[base]=="Off"):  channelNormalization[base]=None
    channelScale[base] = xmlChannel.find('scale').text.strip().title()
    sourcetype= xmlChannel.find('source').attrib['type'].title()
    if (sourcetype=="Array" or sourcetype=="Constant"):
      data = map(float, xmlChannel.find('source').text.strip().split(','))
      channelSources[base] = [ sourcetype, data ]
      if (xmlChannel.find('source').attrib['extend'].title() == "True"):
        channelSizes[base] = -1
      else:
        channelSizes[base] = len(data)
    elif (sourcetype=="File"):
      channelSources[base] = [ sourcetype,  xmlChannel.find('source').text.strip() ]
      if (cacheType == "Particles"):
        channelSizes[base] = numberofparticles
      if (cacheType == "Fluids"):
        channelSizes[base] =  resolution[0]*resolution[1]*resolution[2]

# Global normalization needs to happen now
if Normalization != None:
    print "Finding global minima and maxima"
    for channel in sorted(channelNames.keys()):
      if channelNormalization[channel].title() == "Global":
        minim = 1.0E30
        maxim = -1.0E30
        if channelTypes[channel]=="FVCA":
            dataLength = 3
        else:
            dataLength = 1
        channel_files = sorted(glob.glob(os.path.join(inputpath,inputBaseName+"."+channelSources[channel][1]+"*")))
        for filename in channel_files:
            f=open(filename,'rb')
            data=array.array('f')
            if (channelSizes[channel] > 0):
                bufferSize = dataLength*channelSizes[channel]
            else:
                bufferSize = os.path.getsize(filename)
            data.fromfile(f,bufferSize)
            maxim=max(maxim,max(data))
            minim=min(minim,min(data))
            f.close()
            #print "Normalizing "+channel+" to "+str(minim)+", "+str(maxim)
        channelNormalization[channel]=[minim,maxim]
      elif channelNormalization[channel]!= None and channelNormalization[channel].title() != "Local":
        minim, maxim = map(float, channelNormalization[channel].split(','))
        channelNormalization[channel] = [ minim, maxim ]

# For now, time increment is fixed.
dt = 250

if Verbose: print("Order of out channels: "+str(sorted(channelNames.keys())))
cacheFiles = []
# Let's load and prepare all cache files
for frame in range(1,numFrames+1):
    time = frame * dt
    #    ,inputPath,inputBaseName,frame,cacheStartTime,cacheEndTime,namesDict,sizesDict,typesDict,normDict,scaleDict):
    # Create all the channels for this frame
    #
    channels = []
    #  Header channels for particles
    if (cacheType == "Particles"):
       #Need to find out number of particles first
       if (numberofparticles<0):
            randomChannelName = channelNames.keys()[0]
            channelType = channelTypes[randomChannelName]
            fileName = os.path.join(inputPath,inputBaseName+"."+channelSources[randomChannelName][1]+"."+str(frame).zfill(5))
            if channelType=="FVCA":
                  dataLength = 3
              else:
                  dataLength = 1
            frameParticles = os.path.getsize(source)/(dataLength*4)
       else:
          frameParticles = numberofparticles
       #Particle caches always carry total count and Id channels at the beggining
       channelType = "FBCA"
       channelFullName = channelsBaseName+"_id"
       normalization = None
       scale = "Normal"
       # Ids are invented...they could come from a file ###################
       source = map( float, range(frameParticles) )
       arrayLength = frameParticles
       oneChannel = CacheChannel(channelFullName,channelType,arrayLength,source,normalization,scale)
       channels.append( oneChannel )
       #####
       channelType = "FBCA"
       channelFullName = channelsBaseName+"_count"
       normalization = None
       scale = "Normal"
       source = [float(frameParticles)]
       arrayLength = len(source)
       oneChannel = CacheChannel(channelFullName,channelType,arrayLength,source,normalization,scale)
       channels.append( oneChannel )
       #####
    #  Actual data channels
    for channelName in sorted(channelNames.keys()):
       channelType = channelTypes[channelName]
       channelFullName = channelNames[channelName]
       normalization = channelNormalization[channelName]
       scale = channelScale[channelName]
       if (channelSources[channelName][0]=="Array" or channelSources[channelName][0]=="Constant"):
          source = channelSources[channelName][1]
          #Channel size can be an array extended to all particles
          if (channelSizes[channelName] > 0):
              arrayLength = channelSizes[channelName]
          else:
              arrayLength = frameParticles
          oneChannel = CacheChannel(channelFullName,channelType,arrayLength,source,normalization,scale)
       else:
          source = os.path.join(inputPath,inputBaseName+"."+channelSources[channelName][1]+"."+str(frame).zfill(5))
          if (channelSizes[channelName] > 0):
              arrayLength = channelSizes[channelName]
          else:
              if channelType=="FVCA":
                  dataLength = 3
              else:
                  dataLength = 1
              arrayLength = os.path.getsize(source)/(dataLength*4)
          if (Debug): print ("Making "+channelFullName+", length "+str(arrayLength))
          oneChannel = CacheChannelFromFile(channelFullName,channelType,arrayLength,source,normalization,scale)
       channels.append( oneChannel )
    #  Tailer channels for fluids
    if (cacheType == "Fluids"):
       #These two channels always come at the end of each frame in a Fluid cache
       channelType = "FBCA"
       channelFullName = "resolution"
       normalization = None
       scale = "Normal"
       source = resolution
       arrayLength = len(resolution)
       oneChannel = CacheChannel(channelFullName,channelType,arrayLength,source,normalization,scale)
       channels.append( oneChannel )
       channelType = "FBCA"
       channelFullName = "offset"
       normalization = None
       scale = "Normal"
       source = offset
       arrayLength = len(offset)
       oneChannel = CacheChannel(channelFullName,channelType,arrayLength,source,normalization,scale)
       channels.append( oneChannel )

    aCache = CacheFile(time,time+dt,channels)
    cacheFiles.append( aCache )

# Write the data files
frame=1
for cache in cacheFiles:
    print str(frame)
    fileName = os.path.join(outputpath,outputBaseName+"Frame"+str(frame)+".mc")
    cache.writeDataFilePerFrame(fileName)
    frame += 1


# Write the output XML file
header = """<?xml version="1.0"?>
<Autodesk_Cache_File>
  <cacheType Type="OneFilePerFrame" Format="mcc"/>
  <time Range="250-FINALTIME"/>
  <cacheTimePerFrame TimePerFrame="250"/>
  <cacheVersion Version="2.0"/>
  <extra>nParticle Cache created from binary data</extra>
  <extra>maya 2014 x64</extra>
  <extra>Conversion script by Fernando Cucchietti</extra>
  <Channels>
"""
tailer="""
  </Channels>
</Autodesk_Cache_File>
"""

channelxml="""<channelNUM ChannelName="CHANNELNAME" ChannelType="CHANNELTYPE" ChannelInterpretation="CHANNELINTERPRETATION" SamplingType="Regular" SamplingRate="250" StartTime="250" EndTime="FINALTIME"/>
"""
endtime = numFrames * 250

nc = 0
if (cacheType == "Particles"):
    channels_out_xml=channelxml.replace("NUM","0").replace("CHANNELNAME",channelsBaseName+"_id").replace("CHANNELTYPE","FloatArray").replace("CHANNELINTERPRETATION","id").replace("FINALTIME",str(endtime))
    channels_out_xml=channels_out_xml+channelxml.replace("NUM","1").replace("CHANNELNAME",channelsBaseName+"_count").replace("CHANNELTYPE","FloatArray").replace("CHANNELINTERPRETATION","count").replace("FINALTIME",str(endtime))
    nc=nc+2

for channelName in sorted(channelNames.keys()):
    channelType = channelTypes[channelName]
    if (channelType=="FBCA"):
        ctype = "FloatArray"
    elif(channelType=="FVCA"):
        ctype = "FloatVectorArray"
    channelFullName = channelNames[channelName]
    interpretation = channelFullName.split("_")[1]
    channels_out_xml=channels_out_xml+channelxml.replace("NUM",str(nc)).replace("CHANNELNAME",channelFullName).replace("CHANNELTYPE",ctype).replace("CHANNELINTERPRETATION",interpretation).replace("FINALTIME",str(endtime))
    nc=nc+1

if (cacheType == "Fluids"):
    channels_out_xml=channels_out_xml+channelxml.replace("NUM",str(nc)).replace("CHANNELNAME",channelsBaseName+"_resolution").replace("CHANNELTYPE","FloatArray").replace("CHANNELINTERPRETATION","resolution").replace("FINALTIME",str(endtime))
    channels_out_xml=channels_out_xml+channelxml.replace("NUM",str(nc+1)).replace("CHANNELNAME",channelsBaseName+"_offset").replace("CHANNELTYPE","FloatArray").replace("CHANNELINTERPRETATION","offset").replace("FINALTIME",str(endtime))


fxml = open ( os.path.join(outputpath,outputBaseName+".xml"),'w')
fxml.write(header.replace("FINALTIME",str(endtime)))
fxml.write(channels_out_xml)
fxml.write(tailer)
fxml.close()


