#!/bin/bash -ex
cd /home/ubuntu
wget https://s3.amazonaws.com/mpcs-students/zuomingli/mpcs_capstone.zip
unzip mpcs_capstone.zip
rm mpcs_capstone.zip
cd mpcs_capstone
chmod 400 *.pem
chmod 755 *.sh
sudo cp /home/ubuntu/mpcs_capstone/.aws/* /home/ubuntu/.aws
sudo chown -R ubuntu:ubuntu /home/ubuntu/mpcs_capstone
sudo chown -R ubuntu:ubuntu /home/ubuntu/.aws
sudo -u ubuntu ./mpcs_run.sh &
