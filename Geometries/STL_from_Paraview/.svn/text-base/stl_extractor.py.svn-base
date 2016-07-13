# -*- coding: latin-1 -*-
##############################################################################
#    Copyright (C) 2012 by BSC-CNS                                           #
#    Author: Carlos Tripiana Montes <carlos.tripiana@bsc.es>                 #
#                                                                            #
#    This program is free software; you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation; either version 3 of the License.          #
#                                                                            #
#    This program is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            #
#    GNU General Public License for more details.                            #
#                                                                            #
#    You should have received a copy of the GNU General Public License       #
#    along with this program; if not, visit the following webpage:           #
#    http://www.gnu.org/licenses/gpl.html                                    #
##############################################################################
##############################################################################
#    INTRUCTIONS:                                                            #
#                                                                            #
#    Before executing the script, make sure the state file loads properly.   #
#    Check file paths and options, depending which version of paraview do    #
#    you use.                                                                #
#    Finally test the state file loading it into paraview. If this works     #
#    the script should work.                                                 #
##############################################################################
# Imports
import argparse
import array
import math
import shutil
from paraview.simple import *
# Constants
MAX_DIMENSIONS = 3
# Parse parameters
parser = argparse.ArgumentParser(description = "Process the arguments")
parser.add_argument("stateFile", help = "Path to the state file (PVSM)")
parser.add_argument("outputDir", help = "Path to the output directory (must be writable)")
args = parser.parse_args()
print "STARTING"
# Load the state
paraview.servermanager.LoadState(args.stateFile)
# Make sure the view in the state is the active one
activeView = paraview.simple.GetRenderView()
paraview.simple.SetActiveView(activeView)
# Get the list of sources
sources = paraview.simple.GetSources()
# PROLOG: Create the variables and pipeline objects we will need
rangesList = []
index = 0
surface = paraview.servermanager.filters.ExtractSurface(NonlinearSubdivisionLevel = 1, PieceInvariant = 1)
triangulator = paraview.servermanager.filters.Triangulate()
writer = paraview.servermanager.writers.PSTLWriter(FileType = 2)
calculator = paraview.servermanager.filters.Calculator(AttributeMode = "point_data", CoordinateResults = 1, ReplaceInvalidResults = 0, ReplacementValue = 0.0, ResultArrayName = "POINTS")
# 1st STEP: Get the ranges' values for each visible source
# Iterate over all sources
for source in sources.items():
   # If the source is in the view and it's visible
   representation = paraview.servermanager.GetRepresentation(source[1], activeView)
   if representation != None and representation.Visibility == 1 :
       # Get the data name -> data info
       dataName = representation.ColorArrayName
       dataInfo = source[1].PointData[dataName]
       # If the source has any kind of data associated
       if dataInfo != None :
           lookupTable = representation.LookupTable
           newRange = []
           # Check what type of mapping we should do
           if lookupTable.VectorMode == "Component" :
               # Select the appropriate component
               if lookupTable.VectorComponent == 0 :
                   newRange.append(dataName + "_X")
               elif lookupTable.VectorComponent == 1 :
                   newRange.append(dataName + "_Y")
               elif lookupTable.VectorComponent == 2 :
                   newRange.append(dataName + "_Z")
               else :
                   print "Skipping dimension higher than " + MAX_DIMENSIONS + " for " + source[0][0] + "_" + source[0][1] + "_" + dataName
                   newRange = None
               # endif
               if newRange != None :
                   # If there is a custom range we use it, otherwise we use the temporal (fixed range) max and min limits
                   if lookupTable.ScalarRangeInitialized and lookupTable.LockScalarRange :
                       newRange.append([lookupTable.RGBPoints[0], lookupTable.RGBPoints[-4] ])
                   else :
                       # Look up the input source
                       inputSource = source[1]
                       while "Input" in dir(inputSource) :
                           inputSource = inputSource.Input
                       # endwhile
                       # Is this file an animation or not?
                       if "TimestepValues" in dir(inputSource) and inputSource.TimestepValues.__str__() != "None" :
                           newRange.append([float("+inf"), float("-inf")])
                           # Iterate over the input source steps
                           timeSteps = inputSource.TimestepValues
                           for timeStep in timeSteps :
                               # Go to the step
                               source[1].UpdatePipeline(timeStep)
                               # Get the data info -> data range for this step
                               dataInfo = source[1].PointData[dataName]
                               # Retrieve the range for that component
                               tempRange = dataInfo.GetRange(lookupTable.VectorComponent)
                               # Find the min and max over all steps
                               if tempRange[0] < newRange[1][0] :
                                   newRange[1][0] = tempRange[0]
                               # endif
                               if tempRange[1] > newRange[1][1] :
                                   newRange[1][1] = tempRange[1]
                               # endif
                           # endfor
                       # endif
                       else :
                           # Default limits for this source and component
                           newRange.append(dataInfo.GetRange(lookupTable.VectorComponent) )
                       # endif
                   # endif
                   rangesList.append(newRange)
               else :
                   rangesList.append(None)
               # endif
           elif lookupTable.VectorMode == "Magnitude" :
               # Query the number of dimensions for this data
               numDimensions = source[1].GetDataInformation().DataInformation.GetPointDataInformation().GetArrayInformation(dataName).GetNumberOfComponents()
               # Select the appropriate expresion for the components
               if numDimensions == 1 :
                   newRange.append(dataName)
               elif numDimensions > 1 and numDimensions <= MAX_DIMENSIONS :
                   newRange.append("mag(" + dataName + ")")
               else :
                   print "Skipping dimension higher than " + MAX_DIMENSIONS + " for " + source[0][0] + "_" + source[0][1] + "_" + dataName
                   newRange = None
               # endif
               if newRange != None :
                   # If there is a custom range we use it, otherwise we use the temporal (fixed range) max and min limits
                   if lookupTable.ScalarRangeInitialized and lookupTable.LockScalarRange :
                       newRange.append([lookupTable.RGBPoints[0], lookupTable.RGBPoints[-4] ])
                   else :
                       # Look up the input source
                       inputSource = source[1]
                       while "Input" in dir(inputSource) :
                           inputSource = inputSource.Input
                       # endwhile
                       # Is this file an animation or not?
                       if "TimestepValues" in dir(inputSource) and inputSource.TimestepValues.__str__() != "None" :
                           newRange.append([float("+inf"), float("-inf")])
                           # Iterate over the input source steps
                           timeSteps = inputSource.TimestepValues
                           for timeStep in timeSteps :
                               # Go to the step
                               source[1].UpdatePipeline(timeStep)
                               # Get the data info -> data range for this step
                               dataInfo = source[1].PointData[dataName]
                               # Calculate the range for a scalar or a vector
                               if numDimensions == 1 :
                                   # Retrieve the range for the value
                                   tempRange = dataInfo.GetRange()
                                   # Find the min and max over all steps
                                   if tempRange[0] < newRange[1][0] :
                                       newRange[1][0] = tempRange[0]
                                   # endif
                                   if tempRange[1] > newRange[1][1] :
                                       newRange[1][1] = tempRange[1]
                                   # endif
                               else :
                                   # Retrieve the range for the magnitude
                                   tempRange = dataInfo.GetRange(-1)
                                   # Find the min and max over all steps
                                   if tempRange[0] < newRange[1][0] :
                                       newRange[1][0] = tempRange[0]
                                   # endif
                                   if tempRange[1] > newRange[1][1] :
                                       newRange[1][1] = tempRange[1]
                                   # endif
                               # endif 
                           # endfor
                       # endif
                       else :
                           # Calculate the range for a scalar or a vector
                           if numDimensions == 1 :
                               # Retrieve the range for the value
                               newRange.append(dataInfo.GetRange() )
                           else :
                               # Retrieve the range for the magnitude
                               newRange.append(dataInfo.GetRange(-1) )
                           # endif
                       # endif
                   # endif
                   rangesList.append(newRange)
               else :
                   rangesList.append(None)
               # endif
           else :
               print "Skipping unhandled data mapping " + lookupTable.VectorMode + " for " + source[0][0] + "_" + source[0][1] + "_" + dataName
               newRange = None
           # endif
       else :
           rangesList.append(None)
       # endif
   # endif
# endfor
print "Choosen ranges are: " + rangesList.__str__() + "\n"
# 2nd STEP: Save the geometry for each visible source (and for each step, if it is an animation)
# 3rd STEP: store the facets' vertices' values for each source and step
# Iterate over all sources
for source in sources.items() :
   # If the source is in the view and it's visible
   representation = paraview.servermanager.GetRepresentation(source[1], activeView)
   if representation != None and representation.Visibility == 1 :
       # We only need those sources which have any data associated
       if rangesList[index] != None :
           # Get the data name -> data info
           dataName = representation.ColorArrayName
           dataInfo = source[1].PointData[dataName]
           # If the source has any kind of data associated
           if dataInfo != None :
               # Generate the function to map the data into coordinates (forces interpolation and reduces the size of the data)
               calculator.Function = "iHat * " + rangesList[index][0] + " + jHat * " + rangesList[index][1][0].__str__() + " + kHat * " + rangesList[index][1][1].__str__()
               # Look up the input source
               inputSource = source[1]
               while "Input" in dir(inputSource) :
                   inputSource = inputSource.Input
               # endwhile
               # Is this file an animation or not?
               if "TimestepValues" in dir(inputSource) and inputSource.TimestepValues.__str__() != "None" :
                   # Iterate over the input source steps
                   timeSteps = inputSource.TimestepValues
                   outputMeshFile = args.outputDir + "/" + source[0][0] + "_" + source[0][1] + "_step_"
                   outputDataFile = args.outputDir + "/" + source[0][0] + "_" + source[0][1] + "_" + rangesList[index][0] + "_step_"
                   step = 0
                   for timeStep in timeSteps :
                       # Go to the step
                       source[1].UpdatePipeline(timeStep)
                       print "Extracting mesh: " + outputMeshFile + str(step).zfill(3) + ".stl"
                       # In case the source is not a polygonal mesh
                       surface.Input = source[1]
                       surface.UpdatePipeline(timeStep)
                       triangulator.Input = surface
                       triangulator.UpdatePipeline(timeStep)
                       # Write the binary STL output file for this object and step
                       writer.Input = triangulator
                       writer.FileName = outputMeshFile + str(step).zfill(3)  + "_.stl"
                       writer.UpdatePipeline(timeStep)
                       # Some writers add the number of the step but we are doing the animation by hand
                       try :
                           shutil.move(outputMeshFile + str(step).zfill(3)  + "_0.stl", outputMeshFile + str(step).zfill(3)  + ".stl")
                       except IOError :
                           shutil.move(outputMeshFile + str(step).zfill(3) + "_.stl", outputMeshFile + str(step).zfill(3)  + ".stl")
                       # endtry
                       print "  -> Extracted mesh: " + outputMeshFile + str(step).zfill(3) + ".stl"
                       print "Extracting data: " + outputDataFile + str(step).zfill(3) + ".bin"
                       # Gets the associated data and replaces the coordinates with its value for each point
                       calculator.Input = triangulator
                       calculator.UpdatePipeline(timeStep)
                       # Write the binary STL output file for this data and step
                       writer.Input = calculator
                       writer.FileName = outputDataFile + str(step).zfill(3) + "_.stl"
                       writer.UpdatePipeline(timeStep)
                       # Some writers add the number of the step but we are doing the animation by hand
                       try :
                           shutil.move(outputDataFile + str(step).zfill(3) + "_0.stl", outputDataFile + str(step).zfill(3) + ".bin")
                       except IOError :
                           shutil.move(outputDataFile + str(step).zfill(3) + "_.stl", outputDataFile + str(step).zfill(3) + ".bin")
                       # endtry
                       print "  -> Extracted data: " + outputDataFile + str(step).zfill(3) + ".bin"
                       step = step + 1
                   # endif
               else :
                   outputMeshFile = args.outputDir + "/" + source[0][0] + "_" + source[0][1] + ".stl"
                   outputDataFile = args.outputDir + "/" + source[0][0] + "_" + source[0][1] + "_" + rangesList[index][0]
                   print "Extracting mesh: " + outputMeshFile
                   # In case the source is not a polygonal mesh
                   surface.Input = source[1]
                   surface.UpdatePipeline()
                   triangulator.Input = surface
                   triangulator.UpdatePipeline()
                   # Write the binary STL output file for this object
                   writer.Input = triangulator
                   writer.FileName = outputMeshFile
                   writer.UpdatePipeline()
                   print "  -> Extracted mesh: " + outputMeshFile
                   print "Extracting data: " + outputDataFile + ".bin"
                   # Gets the associated data and replaces the coordinates with its value for each point
                   calculator.Input = triangulator
                   calculator.UpdatePipeline()
                   # Write the binary STL output file for this data
                   writer.Input = calculator
                   writer.FileName = outputDataFile + ".stl"
                   writer.UpdatePipeline()
                   shutil.move(outputDataFile + ".stl", outputDataFile + ".bin")
                   print "  -> Extracted data: " + outputDataFile + ".bin"
               # endif
               print ""
           # endif
       # endif
       index = index + 1
   # endif
# endfor
print "DONE"
