#!/bin/bash

set -eE

if [ "$EUID" -ne 0 ]
  then echo "Please run the script as root"
  exit
fi

IMAGE_VERSION=$1

cd plugins/
tar -zcvf SLURM-Integration_1_0_0_${IMAGE_VERSION}.tgz SLURM-Integration