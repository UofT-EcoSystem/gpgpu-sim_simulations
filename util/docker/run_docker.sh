docker run --privileged --hostname docker.gpusim -dit --runtime=nvidia -v /scratch/serina/:/mnt --ipc=host --name gpusim gpusim_serina
docker exec -it gpusim bash
