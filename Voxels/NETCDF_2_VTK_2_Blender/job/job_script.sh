#!/bin/bash

ulimit -s unlimited

export BASENAME=$(basename "$INPUT_FILE" .nc)
if [[ -n "$DIMENSIONS_TO_BE_REDUCED" ]]; then
  module load NCO/4.5.1 &> /dev/null
  export OMP_NUM_THREADS=$NCORES
  rm -f "$OUTPUT_DIR/${BASENAME}_reduced.nc"
  ncwa -t $OMP_NUM_THREADS -a $DIMENSIONS_TO_BE_REDUCED "$INPUT_FILE" "$OUTPUT_DIR/${BASENAME}_reduced.nc"
  unset OMP_NUM_THREADS
  module unload NCO/4.5.1 &> /dev/null
  export INPUT_FILE="$OUTPUT_DIR/${BASENAME}_reduced.nc"
  export BASENAME="${BASENAME}_reduced"
fi

TOTAL_FRAMES=$(($END_FRAME - $START_FRAME + 1))
export NFIELDS=$(echo "$VARIABLES_TO_BE_EXTRACTED" | wc -l)
NFILES=$(($TOTAL_FRAMES * $NFIELDS))
NFILES_PER_TASK=$(($NFILES / $NTASKS))
if [ $(($NFILES % $NTASKS)) -ne 0 ]; then
  let NFILES_PER_TASK=$(($NFILES_PER_TASK + 1))
fi

declare -a FIELDS
I=0
for FIELD in $VARIABLES_TO_BE_EXTRACTED; do
  FIELDS[$I]=$FIELD
  I=$(($I + 1))
done

typeset FRAMELIST[$(($NTASKS * $NFILES_PER_TASK))]
for NODE in $(seq 0 $(($NNODES - 1)) ); do
  for TASK in $(seq 0 $(($NTASKS_PER_NODE - 1)) ); do
    for FILE in $(seq 0 $(($NFILES_PER_TASK - 1)) ); do
      INDEX=$(($NODE * $NTASKS_PER_NODE * $NFILES_PER_TASK + $TASK * $NFILES_PER_TASK + $FILE))
      FRAME=$(($NTASKS * $FILE + $NODE * $NTASKS_PER_NODE + $TASK))
      FIELD=${FIELDS[$(($FRAME / $TOTAL_FRAMES))]}
      if [ $FRAME -lt $NFILES ]; then
        FRAME=$(($START_FRAME + $FRAME % $TOTAL_FRAMES))
        FRAMELIST[$INDEX]="$FRAME|$FIELD"
      else
        FRAMELIST[$INDEX]="-1|"
      fi
    done
  done
done

rm -f "$OUTPUT_DIR/.frames.list"
for NODE in $(seq 0 $(($NNODES - 1)) ); do
  for TASK in $(seq 0 $(($NTASKS_PER_NODE - 1)) ); do
    START=$(($NODE * $NTASKS_PER_NODE * $NFILES_PER_TASK + $TASK * $NFILES_PER_TASK))
    ROW=${FRAMELIST[@]:$START:$NFILES_PER_TASK}
    echo $ROW >> "$OUTPUT_DIR/.frames.list"
  done
done

export HEADER=$(ncdump -h "$INPUT_FILE")
rm -rf "$OUTPUT_DIR/VTK"
mkdir -p "$OUTPUT_DIR/VTK"
mpirun -genvall -envall "$(dirname $(readlink -e $0) )/vtk/task.sh"
rm -rf "$OUTPUT_DIR/BVOX"
mkdir -p "$OUTPUT_DIR/BVOX"
mpirun -genvall -envall "$(dirname $(readlink -e $0) )/bvox/prolog_task.sh"
mpirun -genvall -envall "$(dirname $(readlink -e $0) )/bvox/task.sh"
mpirun -genvall -envall "$(dirname $(readlink -e $0) )/bvox/epilog_task.sh"
rm -f "$OUTPUT_DIR/.frames.list" "$OUTPUT_DIR/BVOX/"*.bin

if [[ -n "$EXTRACT_DEM_VARIABLE" ]]; then
  mkdir -p "$OUTPUT_DIR/TIFF"
  $(dirname $(readlink -e $0) )/dem/task.sh
fi
