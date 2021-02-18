#!/bin/bash


mkdir ortho
mkdir raw


module load miniconda
conda activate GIS

jobs=0
for i in {0..29}; do
    python orthogonalize.py $i &

    ((jobs++))
    if (($jobs % 20 == 0)); then
        wait
    fi
done
wait

conda deactivate
