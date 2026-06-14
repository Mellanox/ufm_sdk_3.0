#!/bin/bash
#
# Copyright © 2009-2026 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
# Build (and optionally push) the ufm-state-mirror image.
#
# Usage:
#   build/docker_build.sh [VERSION] [OUT_DIR] [RANDOM_HASH]
#
#   VERSION      image tag; defaults to the component VERSION file, else "latest".
#   OUT_DIR      if set, the built image is `docker save`d as a .img.gz here.
#   RANDOM_HASH  appended to the saved artifact name for CI uniqueness.
#
# Env:
#   REGISTRY     image registry/namespace prefix (default: mellanox).
#   PUSH         "y" to `docker push` the tagged image after build.

set -eE

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
COMPONENT_DIR="$(realpath "${SCRIPT_DIR}/..")"

IMAGE_NAME="ufm-state-mirror"
REGISTRY="${REGISTRY:-mellanox}"

VERSION="$1"
OUT_DIR="$2"
RANDOM_HASH="$3"

if [ -z "${VERSION}" ]; then
    if [ -f "${COMPONENT_DIR}/VERSION" ]; then
        VERSION="$(tr -d '\n' < "${COMPONENT_DIR}/VERSION")"
    else
        VERSION="latest"
    fi
fi

IMAGE="${REGISTRY}/${IMAGE_NAME}:${VERSION}"

echo "COMPONENT_DIR : [${COMPONENT_DIR}]"
echo "IMAGE         : [${IMAGE}]"
echo "OUT_DIR       : [${OUT_DIR:-<none>}]"
echo "RANDOM_HASH   : [${RANDOM_HASH:-<none>}]"
echo " "

# The Dockerfile COPYs `requirements.txt` and `state_mirror/` relative to the
# build context, so the context is the component root (not build/).
docker build \
    --network host \
    --no-cache \
    --pull \
    --compress \
    -f "${SCRIPT_DIR}/Dockerfile" \
    -t "${IMAGE}" \
    "${COMPONENT_DIR}"

docker images | grep "${REGISTRY}/${IMAGE_NAME}" || true

if [ -n "${OUT_DIR}" ]; then
    mkdir -p "${OUT_DIR}"
    if [ "${VERSION}" = "0.0.00-0" ] && [ -n "${RANDOM_HASH}" ]; then
        artifact="${IMAGE_NAME}_${VERSION}-${RANDOM_HASH}-docker.img.gz"
    else
        artifact="${IMAGE_NAME}_${VERSION}-docker.img.gz"
    fi
    echo "Saving image to ${OUT_DIR}/${artifact}"
    docker save "${IMAGE}" | gzip > "${OUT_DIR}/${artifact}"
fi

if [ "${PUSH}" = "y" ] || [ "${PUSH}" = "Y" ]; then
    echo "Pushing ${IMAGE}"
    docker push "${IMAGE}"
fi

echo "Done: ${IMAGE}"
