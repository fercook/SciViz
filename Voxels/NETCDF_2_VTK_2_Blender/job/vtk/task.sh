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
    FIELD=$(echo "$FRAME" | cut -d"|" -f2)
    DIMENSIONS="($(echo "$HEADER" | grep "$FIELD(.*)" | cut -d"(" -f2 | cut -d")" -f1 | sed -e "s/time, //g" -e "s/time//g"))"
    pvpython "$(dirname $(readlink -e $0) )/paraview/NC2VTKVoxel.py" "$INPUT_FILE" "$OUTPUT_DIR/VTK" "$FIELD" "$DIMENSIONS" $FRAME_NUM $XFACTOR $YFACTOR $ZFACTOR
  fi
done
