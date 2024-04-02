#!/bin/bash
MACHINE_NAME=${1:-batch}
MEMORY=${2:-64GB}

srun -K \
-p $MACHINE_NAME \
--ntasks 1 \
--mem="$MEMORY" \
--container-image='/netscratch/skhan/enroot/default.sqsh' \
--container-mounts=/home:/home,/netscratch:/netscratch,/ds:/ds,/dev/fuse:/dev/fuse \
--container-workdir=$(pwd) \
--export="NCCL_SOCKET_IFNAME=bond,NCCL_IB_HCA=mlx5" \
--time=24:00:00 \
--pty /bin/bash
