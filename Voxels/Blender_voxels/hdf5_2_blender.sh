#!/bin/sh
#
var=$1
x=$2
y=$3
z=$4

for f in *.h5;do h5dump -d /${var} -b LE -o raw-$f $f;done

./raws_to_bvox.py raw ${var}.bvox -x $x -y $y -z $z -n -V

rm raw*

