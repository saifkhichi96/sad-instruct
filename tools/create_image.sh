srun \
    --mem=64G \
    --container-image=/netscratch/enroot/nvcr.io_nvidia_pytorch_23.07-py3.sqsh \
    --container-save=/netscratch/$USER/enroot/situational.sqsh \
    --container-mounts=/dev/fuse:/dev/fuse,/netscratch/$USER:/netscratch/$USER,"`pwd`":"`pwd`" \
    --container-workdir="`pwd`" \
    bash scripts/install.sh
