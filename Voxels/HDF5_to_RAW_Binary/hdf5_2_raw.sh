#!/bin/sh
#
var=$1
x=$2
y=$3
z=$4
root=$5 

i=0
for f in *.h5;do h5dump -d /${var} -b LE -o root.${var}.$(printf "%05d" "$i") $f;done
