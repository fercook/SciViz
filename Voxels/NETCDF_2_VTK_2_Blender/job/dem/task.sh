#!/bin/bash

ulimit -s unlimited

module purge &> /dev/null
module load PARAVIEW/4.3.1 &> /dev/null

DIMENSIONS="($(echo "$HEADER" | grep "$EXTRACT_DEM_VARIABLE(.*)" | cut -d"(" -f2 | cut -d")" -f1 | sed -e "s/time, //g" -e "s/time//g"))"
pvpython "$(dirname $(readlink -e $0) )/paraview/NC2VTKDEM.py" "$INPUT_FILE" "$OUTPUT_DIR/VTK" "$EXTRACT_DEM_VARIABLE" "$DIMENSIONS" "$DEM_MASSAGE" $DEM_XFACTOR $DEM_YFACTOR $DEM_ZFACTOR
pvpython "$(dirname $(readlink -e $0) )/paraview/VTKDEM2TIFF.py" "$OUTPUT_DIR/VTK/$(basename $INPUT_FILE .nc)_$EXTRACT_DEM_VARIABLE.vtk" "$OUTPUT_DIR/TIFF"
