The python script is configured from the xml file, look at the template. Here is some info on how to prepare the binary files that go into the script, and some general Maya info con particle Caches

File names
==========

Binary files must be named in the following way

BaseName.CHANNEL.frame
inputXMLFileName = "" # Read info from input file
outputBaseName = "lleno"
channelsBaseName = "fluidShape1"
inputBaseName = "color"
numFrames = 24
resolution = [3,4,5]
boxSize = [3,4,5]
channelNames = {} # CHANNEL, MayaChannelName
channelNames['DENSITY']=channelsBaseName+'_density'
channelNames['TEMPERATURE']=channelsBaseName+'_temperature'

Input file example (XML)
======================
```xml
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
```

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



Cacheable properties can be found at
http://download.autodesk.com/global/docs/maya2014/en_us/index.html?url=files/GUID-3130B434-C0D5-4FF7-94A4-7F056ADF712A.htm,topicNumber=d30e555354,hash=WS73099CC142F48755558158A8119D88FB23C-62A9

