import os
import os.path
import getopt
import sys
from xml.etree import cElementTree
import re
import array
import glob
import math

"""
File names
==========

Binary files must be named in the following way

BaseName.CHANNEL.frame

# Fill in necessary information in the input XML file

Input file format (XML)
======================

<MayaCache name="NameOfCacheInMaya">

<properties>
  <frames>100</frames>
  <size> 2.0, 2.0, 3.0 </size>
  <resolution> x, y z </resolution>
  <offset> 0,0,0 </offset>
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
  <channel name="SomeProblemDomainName">
    <interpretation> density </interpretation>
    <type> FBCA </type>
    <extension>CHANNEL</extension>
    <normalization> Off|Global|Local </normalization>
    <scale> Normal | Logarithmic </scale>
  </channel>
  <channel name="SomeProblemDomainName">
    <interpretation> temperature </interpretation>
    <type> FVCA </type>
    <extension>CHANNEL</extension>
    <normalization> Off|Global|Local </normalization> (notice normalization is a range like:  10.0, 230.0  )
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

//  |---CACH (Group)	// Header
//  |     |---VRSN		// Version Number (char*)
//  |     |---STIM		// Start Time of the Cache File (int)
//  |     |---ETIM		// End Time of the Cache File (int)
//  |
//  |---MYCH (Group)	// 1st Time 
//  |     |---TIME		// Time (int)
//  |     |---CHNM		// 1st Channel Name (char*)
//  |     |---SIZE		// 1st Channel Size
//  |     |---DVCA		// 1st Channel Data (Double Vector Array)
//  |     |---CHNM		// n-th Channel Name
//  |     |---SIZE		// n-th Channel Size
//  |     |---DVCA		// n-th Channel Data (Double Vector Array)
//  |     |..
//  |
//  |---MYCH (Group)	// 2nd Time 
//  |     |---TIME		// Time
//  |     |---CHNM		// 1st Channel Name
//  |     |---SIZE		// 1st Channel Size
//  |     |---DVCA		// 1st Channel Data (Double Vector Array)
//  |     |---CHNM		// n-th Channel Name
//  |     |---SIZE		// n-th Channel Size
//  |     |---DVCA		// n-th Channel Data (Double Vector Array)
//  |     |..
//  |
//  |---..
//	|
//

In a multiple file caches, the only difference is that after the 
header "CACH" group, there is only one MYCH group and there is no 
TIME chunk.	In the case of one file per frame, the time is part of 
the file name - allowing Maya to scan at run time to see what data 
is actually available, and it allows users to move data in time by 
manipulating the file name.  

!Note that it's not necessary to have data for every channel at every time.  

"""

#Yes there are global variables, don't mess with me

Verbose = True

platform = sys.platform
needSwap = False
#This code does not work...
if re.compile("win").match(platform) != None :
    needSwap = True            
if re.compile("linux").match(platform) != None :
    needSwap = True

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


class CacheChannel:
    name = ""
    type = ""
    typeLength = 0
    arrayLength = 0
    binaryDataFile = ""
    maxBufferLength = 400000
    normalization = None
    scale = None
    def __init__(self,channelName,channelType,arrayLength,binaryDataFile,normalization=None,scale=None):
        self.name = channelName
        self.type = channelType                
        self.arrayLength = arrayLength
        self.binaryDataFile = binaryDataFile
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

        # And now write the actual channel data
        if self.binaryDataFile == "resolution":
            data = array.array('f')
            for coord in resolution:
                data.append(coord)
            if needSwap:
                data.byteswap()
            data.tofile(outFile)
        elif (self.binaryDataFile == "offset"):
            data = array.array('f')
            for coord in offset:
                data.append(coord)
            if needSwap:
                data.byteswap()
            data.tofile(outFile)
        else:
            if self.normalization == "Local":
                inFile = open(self.binaryDataFile,"rb")
                datain = array.array('f')
                minim = min(datain)
                maxim = max(datain)
                self.normalization = [minim,maxim]
                inFile.close()
                datain = array.array('f')
            inFile = open(self.binaryDataFile,"rb")
            bytesRead = 0
            while bytesRead < bufferLength:
                datain = array.array('f')
                byteChunk = min(self.maxBufferLength, bufferLength-bytesRead)/4
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
                if needSwap:
                    dataout.byteswap()
                dataout.tofile(outFile)
                bytesRead += byteChunk*4
            inFile.close()

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
            return blockSize

        
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
    def __init__(self,inputPath,inputBaseName,frame,cacheStartTime,cacheEndTime,namesDict,sizesDict,typesDict,normDict,scaleDict):

        self.cacheStartTime = cacheStartTime
        self.cacheEndTime = cacheStartTime
        self.channels = []
        # find all channel files that start with inputBaseName for this frame
        channel_files = sorted(glob.glob(os.path.join(inputPath,inputBaseName+"*"+str(frame).zfill(5))))
        #        print str(frame)
        #        print channel_files
        if (len(channel_files)==0):
            print ("ERROR: No channel files for frame "+str(frame))
            print "Searched : "+inputPath+inputBaseName+"*"+str(frame).zfill(5)
            exit()
        #  create channels associated to the files found
        for fileName in channel_files:
            channelName = os.path.basename(fileName).split('.')[1]
            if channelName in namesDict.keys():
                channelType = typesDict[channelName]
                arrayLength = sizesDict[channelName][0]*sizesDict[channelName][1]*sizesDict[channelName][2]
                channelFullName = namesDict[channelName]
                normalization = normDict[channelName]
                scale = scaleDict[channelName]
                oneChannel = CacheChannel(channelFullName,channelType,arrayLength,filename,normalization,scale)
                self.channels.append( oneChannel )
            else:
                print "WARNING: Found some strangely named channel "+channelName
            #
        #Create resolution and offset channels
        channelFullName = channelsBaseName+"_resolution"
        channelType = "FBCA"
        arrayLength = 3
        fileName = "resolution"
        oneChannel = CacheChannel(channelFullName,channelType,arrayLength,fileName,None,None)
        self.channels.append( oneChannel )
        channelFullName = channelsBaseName+"_offset"
        channelType = "FBCA"
        arrayLength = 3
        fileName = "offset"
        oneChannel = CacheChannel(channelFullName,channelType,arrayLength,fileName,None,None)
        self.channels.append( oneChannel )
        for chan in self.channels:
            print "Channel created: "+chan.name+", file: "+chan.binaryDataFile
            #print "Created "+str(len(self.channels))+" channels"
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
    print "python MayaCacheCreator.py -f input.xml \n"

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
resolution = map ( int , xmlProperties.find('resolution').text.split(',') )
boxSize = map ( float , xmlProperties.find('size').text.split(',') ) 
offset = map ( float , xmlProperties.find('size').text.split(',') ) 
Normalization = xmlProperties.find('normalization').text.strip().title()
if Normalization == "Off":
    Normalization = None

#input output file names
xmlFiles = xmlRoot.find('files')
outputBaseName = xmlFiles.find('output').find('basename').text.strip()
outputpath = xmlFiles.find('output').find('path').text.strip()
inputBaseName = xmlFiles.find('input').find('basename').text.strip()
inputpath = xmlFiles.find('input').find('path').text.strip()
mayaXMLFile = xmlFiles.find('cacheXML').find('basename').text.strip()

#Channel information
xmlChannels = xmlRoot.find('channels')
channelNames = {}
channelSizes = {}
channelTypes = {}
channelNormalization = {}
channelScale = {}
channelsBaseName = xmlRoot.attrib['name'].strip()
for xmlChannel in xmlChannels:
    print "Found channel "+xmlChannel.attrib['name'].strip()
    base= xmlChannel.find('extension').text.strip()
    channelNames[base] = channelsBaseName+'_'+xmlChannel.find('interpretation').text.strip()
    channelSizes[base] =resolution
    channelTypes[base] = xmlChannel.find('type').text.strip()
    channelNormalization[base] = xmlChannel.find('normalization').text.strip()
    channelScale[base] = xmlChannel.find('scale').text.strip().title()
    

if Normalization != None:
    print "Finding global minima and maxima"
    for channel in channelNames.keys():
      if channelNormalization[channel].title() == "Global":
        minim = 1.0E30
        maxim = -1.0E30
        if channelTypes[channel]=="FVCA":
            dataLength = 3
        else:
            dataLength = 1
        bufferSize = dataLength*channelSizes[channel][0]*channelSizes[channel][1]*channelSizes[channel][2]
        channel_files = sorted(glob.glob(os.path.join(inputpath,inputBaseName+"."+channel+"*")))
        for filename in channel_files:
            f=open(filename,'rb')
            data=array.array('f')
            data.fromfile(f,bufferSize)
            maxim=max(maxim,max(data))
            minim=min(minim,min(data))
            f.close()
            #print "Normalizing "+channel+" to "+str(minim)+", "+str(maxim)
        channelNormalization[channel]=[minim,maxim]
      elif channelNormalization[channel].title() != "Local":
        minim, maxim = map(float, channelNormalization[channel].split(','))
        channelNormalization[channel] = [ minim, maxim ]
        
# For now, time increment is fixed.
dt = 250

cacheFiles = []
# Let's load and prepare all cache files
for frame in range(1,numFrames+1):
    time = frame * dt
    aCache = CacheFile(inputpath,inputBaseName,frame,time,time+dt,channelNames,channelSizes,channelTypes,channelNormalization,channelScale)
    cacheFiles.append( aCache )

# Write the output XML file
# TO-DO

# Write the data files
frame=1    
for cache in cacheFiles:
    print str(frame)
    fileName = os.path.join(outputpath,outputBaseName+"Frame"+str(frame)+".mc")
    cache.writeDataFilePerFrame(fileName)
    frame += 1
