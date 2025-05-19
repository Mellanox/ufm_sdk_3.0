#!/bin/bash

set -eE

# Default number of simulators
N=${1:-2}

# Create network if it doesn't exist
if docker network ls | grep -q gnmi_net; then
    echo "Network gnmi_net already exists"
else
    echo "Creating Docker network 'gnmi_net'..."
    docker network create --subnet=172.20.0.0/16 --gateway=172.20.0.1 gnmi_net
fi

# Stop and remove existing containers
echo "Stopping existing simulators..."
docker ps -a | grep gnmi-simulator- | awk '{print $1}' | xargs -r docker rm -f

# Build the image
echo "Building simulator image..."
docker build -t tests-gnmi-simulator -f tests/Dockerfile .

# Start N containers
echo "Starting $N simulators..."
for i in $(seq 1 $N); do
    # Calculate IP address using multiple octets to support more than 255 containers
    THIRD_OCTET=$((i / 256))
    FOURTH_OCTET=$((i % 256))
    IP="172.20.$THIRD_OCTET.$FOURTH_OCTET"
    NAME="gnmi-simulator-$i"
    
    echo "Starting $NAME with IP $IP..."
    docker run -d \
        --name $NAME \
        --network gnmi_net \
        --ip $IP \
        tests-gnmi-simulator
done

# Show running containers
echo -e "\nRunning simulators:"
docker ps | grep gnmi-simulator- 