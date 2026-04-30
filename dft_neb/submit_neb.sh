#!/bin/bash
#SBATCH --job-name=neb_Li2In2GeS6
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=32          # 7 images × 4 cores + 4 spare = 32 (total = IMAGES × NCORE)
#SBATCH --time=48:00:00
#SBATCH --partition=regular           # replace with your partition name
#SBATCH --output=neb_%j.out
#SBATCH --error=neb_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=your@email.com    # replace with your email

# --- Environment ---
module load vasp/6.3.2-vtst            # or your VASP version with VTST patch
# If VTST not patched into VASP, comment out IOPT in INCAR_neb and use IBRION=3

# --- Parallelism for NEB ---
# VASP NEB distributes one image per MPI group.
# With 5 images and 4 cores/image: total = (5 + 2) × 4 = 28 cores
# Endpoints (00 and last dir) are typically fixed — set LNEBCELL=.FALSE.
export OMP_NUM_THREADS=1

# --- Run ---
CANDIDATE=Li2In2GeS6     # change to Li2In2SiS6 or LiInS2 for other candidates
NEB_DIR="neb_${CANDIDATE}"

cd "$NEB_DIR" || exit 1

echo "Starting NEB for ${CANDIDATE} at $(date)"
srun vasp_std
echo "Finished at $(date)"

# --- Post-processing (optional, requires nebresults.pl or vaspkit) ---
# nebresults.pl     # VTST post-processing script
# vaspkit -task 611 # vaspkit NEB analysis

# --- Quick check from OUTCAR ---
grep "climbing" */OUTCAR | head -5
grep "FORCES:" */OUTCAR | tail -10

echo "Max force in each image:"
for d in 0[1-9] [1-9][0-9]; do
    [ -f "$d/OUTCAR" ] && tail -1 "$d/OUTCAR" | awk -v img="$d" '{print img": "$NF}'
done
