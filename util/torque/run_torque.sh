#!/bin/sh

# start server
sudo /opt/local/sbin/pbs_server 
sudo /etc/init.d/pbs_mom
sudo /etc/init.d/pbs_sched


qsub torque.sim

qstat

sleep 5

ls ~/run
cat ~/run/bar3.txt
