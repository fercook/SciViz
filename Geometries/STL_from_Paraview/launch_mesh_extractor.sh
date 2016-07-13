#!/bin/bash

# @ job_name = mesh_extractor
# @ initialdir = ./
# @ output = ./mesh_extractor_%j.out
# @ error = ./mesh_extractor_%j.err
# @ wall_clock_limit = 01:00:00
# @ total_tasks = 1
# @ cpus_per_task = 12
# @ tasks_per_node = 1
# @ gpus_per_node = 0

# 1 NODE

/gpfs/apps/NVIDIA/PARAVIEW/3.14.1/RUN/srun_mesh_extractor PATH_TO_FILE/state_file.pvsm OUTPUT_DIR

#

