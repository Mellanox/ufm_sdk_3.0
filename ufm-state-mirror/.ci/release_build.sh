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
# Release helper for UFM_PLUGINS_SDK_RELEASE.
#
# Usage:
#   ufm-state-mirror/.ci/release_build.sh <VERSION> <OUT_DIR>

set -eE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
COMPONENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

VERSION="$1"
OUT_DIR="$2"
IMAGE_NAME="ufm-state-mirror"

if [ -z "${VERSION}" ] || [ -z "${OUT_DIR}" ]; then
    echo "Usage: $0 <VERSION> <OUT_DIR>"
    exit 2
fi

EXPECTED_VERSION="$(tr -d '\n' < "${COMPONENT_DIR}/VERSION")"
if [ "${VERSION}" != "${EXPECTED_VERSION}" ]; then
    echo -e "Error: ufm-state-mirror release version must match ufm-state-mirror/VERSION."
    echo -e "PLUGIN_VERSION: ${VERSION}"
    echo -e "Expected: ${EXPECTED_VERSION}"
    exit 1
fi

ARTIFACT="${OUT_DIR}/${IMAGE_NAME}_${VERSION}-docker.img.gz"
HASHED_ARTIFACT_PATTERN="${OUT_DIR}/${IMAGE_NAME}_${VERSION}-"*-docker.img.gz
if [ -e "${ARTIFACT}" ] || { [ "${VERSION}" = "0.0.00-0" ] && ls ${HASHED_ARTIFACT_PATTERN} >/dev/null 2>&1; }; then
    echo -e "A build for ${IMAGE_NAME} ${VERSION} already exists."
    echo -e "Path: ${ARTIFACT}"
    if [ "${VERSION}" = "0.0.00-0" ]; then
        echo -e "Path: ${HASHED_ARTIFACT_PATTERN}"
    fi
    exit 1
fi

mkdir -p "${OUT_DIR}"
cd "${COMPONENT_DIR}/build"
bash -x ./docker_build.sh "${VERSION}" "${OUT_DIR}"
