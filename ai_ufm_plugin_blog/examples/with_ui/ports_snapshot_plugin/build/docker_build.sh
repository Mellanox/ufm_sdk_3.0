#!/bin/bash
set -euo pipefail

PLUGIN_NAME=ports_snapshot
IMAGE_NAME=ufm-plugin-${PLUGIN_NAME}:latest
OUTPUT=build/ufm-plugin-${PLUGIN_NAME}_latest-docker.img.gz

docker build --build-arg PLUGIN_NAME="${PLUGIN_NAME}" -t "${IMAGE_NAME}" -f build/Dockerfile .
docker save "${IMAGE_NAME}" | gzip > "${OUTPUT}"
echo "Created $OUTPUT"
