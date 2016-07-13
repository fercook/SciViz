#!/bin/bash

ulimit -s unlimited

TASK=$(($PMI_RANK % $NTASKS_PER_NODE))
SLOT=$(($PMI_RANK / $NTASKS_PER_NODE + $TASK * $NNODES))

sleep $(($TASK * 2))

module purge &> /dev/null
module load PARAVIEW/4.3.1 &> /dev/null

FRAMES=$(cat "$OUTPUT_DIR/.frames.list" | awk 'FNR == '$(($SLOT + 1)) )
for FRAME in $FRAMES; do
  FRAME_NUM=$(echo "$FRAME" | cut -d"|" -f1)
  if [[ $FRAME_NUM -ge $START_FRAME ]]; then
    INDEX=$(printf "%05d" $FRAME_NUM)
    FIELD=$(echo "$FRAME" | cut -d"|" -f2)
    pvpython "$(dirname $(readlink -e $0) )/paraview/VTKVoxel2BVOX.py" "$OUTPUT_DIR/VTK/${BASENAME}_${FIELD}_$INDEX.vtk" "$OUTPUT_DIR/BVOX"
  fi
done
