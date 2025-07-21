#!/bin/bash

echo "Stopping and removing all gnmi simulator containers..."
docker ps -a | grep gnmi-simulator- | awk '{print $1}' | xargs -r docker rm -f

echo -e "\nRemaining containers:"
docker ps | grep gnmi-simulator- 