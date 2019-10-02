#!/bin/sh

# start server
sudo /opt/local/sbin/pbs_server 
sudo /etc/init.d/pbs_mom start
sudo /etc/init.d/pbs_sched start


cd run
/opt/local/bin/qsub torque.sim

/opt/local/bin/qstat

sleep 5

ls ~/run
cat ~/run/bar3.txt
