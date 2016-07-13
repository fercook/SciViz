#!/bin/bash

ulimit -s unlimited

TASK=$(($PMI_RANK % $NTASKS_PER_NODE))
SLOT=$(($PMI_RANK / $NTASKS_PER_NODE + $TASK * $NNODES))

sleep $(($TASK * 2))

if [[ $SLOT -lt $NFIELDS ]]; then
  module purge &> /dev/null
  module load PARAVIEW/4.3.1 &> /dev/null
  
  I=0
  for FIELD in $VARIABLES_TO_BE_EXTRACTED; do
    if [[ $I -eq $SLOT ]]; then
      pvpython "$(dirname $(readlink -e $0) )/paraview/VTKVoxel2BVOX_prolog.py" "$OUTPUT_DIR/VTK/${BASENAME}_${FIELD}_" ".vtk" "$OUTPUT_DIR/BVOX" $START_FRAME $END_FRAME
      break
    fi
    I=$(($I + 1))
  done
fi
