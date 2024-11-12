#!/bin/bash

#SBATCH --job-name=process_fanfics
#SBATCH --array=0-39
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --output=/home/tripakis.m/data-research/fanfic/logs/job_%A_%a.out
#SBATCH --error=/home/tripakis.m/data-research/fanfic/logs/job_%A_%a.err
#SBATCH --time=1-00:00:00

# Load modules or activate environments as needed
conda activate fanfic

# Run the worker script with the SLURM task ID
python worker.py 03.24-09.24 $SLURM_ARRAY_TASK_ID
