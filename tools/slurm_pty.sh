srun \
    --mem=32G \
    --container-image=/netscratch/$USER/enroot/situational.sqsh \
    --container-mounts=/dev/fuse:/dev/fuse,/netscratch/$USER:/netscratch/$USER,"`pwd`":"`pwd`,/ds-av:/ds-av" \
    --container-workdir="`pwd`" \
    --pty bash
