#!/bin/sh
#

if [ $# -eq 0]; then
  echo "No arguments provided"
  echo "Usage: ./hdf5_2_raw.sh VARNAME OUTPUTROOTNAME"
  echo "Will convert ALL .h5 files in a directory"
  exit 1
fi

var=$1
root=$2 

i=0
for f in *.h5;do h5dump -d /${var} -b LE -o ${root}.${var}.$(printf "%05d" "$i") $f;done
