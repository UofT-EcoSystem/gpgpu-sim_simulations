#!/bin/sh

if [ "$#" -lt 1 ]; then
  echo "Usage install_torque.sh num_cores"
fi

echo "Installing torque and configure server to have $1 cores."

# extract/copy files
sudo ./torque-package-mom-linux-x86_64.sh --install
sudo ./torque-package-server-linux-x86_64.sh --install
sudo ldconfig
sudo mkdir /opt/local/bin/
sudo tar xzvf opt-local-bin.tgz -C /
sudo cp trqauthd /opt/local/sbin
sudo cp debian.trqauthd /etc/init.d/trqauthd
sudo cp debian.pbs_mom /etc/init.d/pbs_mom
sudo cp debian.pbs_sched /etc/init.d/pbs_sched

# torque configuration
hostname | sudo tee /var/spool/torque/server_name
echo y | sudo /opt/local/sbin/pbs_server -t create
sudo /etc/init.d/trqauthd start

sleep 20

sudo /opt/local/bin/qmgr -c "set server scheduling=true"
sudo /opt/local/bin/qmgr -c "create queue batch queue_type=execution"
sudo /opt/local/bin/qmgr -c "set queue batch started=true"
sudo /opt/local/bin/qmgr -c "set queue batch enabled=true"
sudo /opt/local/bin/qmgr -c "set queue batch resources_default.nodes=1"
sudo /opt/local/bin/qmgr -c "set queue batch resources_default.walltime=3600"
sudo /opt/local/bin/qmgr -c "set server default_queue=batch"
sudo /opt/local/bin/qterm

echo "pbs_server = 127.0.0.1" | sudo tee /var/spool/torque/mom_priv/config
echo "localhost np=4" | sudo tee /var/spool/torque/server_priv/nodes
echo "`hostname` np=$1" | sudo tee -a /var/spool/torque/server_priv/nodes

