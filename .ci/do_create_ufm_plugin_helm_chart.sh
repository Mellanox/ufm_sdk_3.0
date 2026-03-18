#!/bin/bash
# Package the ufm-plugin Helm chart (no Docker or config extraction).
# Usage: do_create_ufm_plugin_helm_chart.sh <UFM_HELM_VERSION> [ARTIFACT_PATH]
set -e

UFM_HELM_VERSION="${1}"
ARTIFACT_PATH="${2:-/tmp/ufm-helm}"

if [ -z "${UFM_HELM_VERSION}" ]; then
    echo "ERROR: UFM_HELM_VERSION is required"
    echo "Usage: $0 <UFM_HELM_VERSION> [ARTIFACT_PATH]"
    exit 1
fi

if [ -z "${WORKSPACE}" ]; then
    WORKSPACE=$(pwd)
    export WORKSPACE
fi

echo "========================================="
echo "Creating UFM Plugin Helm Chart"
echo "========================================="
echo "Version: ${UFM_HELM_VERSION}"
echo "Output:  ${ARTIFACT_PATH}"
echo "========================================="

if [ ! -d "${WORKSPACE}/k8s/helm/ufm-plugin" ]; then
    echo "ERROR: ufm-plugin chart not found at k8s/helm/ufm-plugin"
    exit 1
fi

mkdir -p "${ARTIFACT_PATH}"
cd "${WORKSPACE}/k8s/helm"
helm package ufm-plugin --version "${UFM_HELM_VERSION}" --app-version "${UFM_HELM_VERSION}"
cp "ufm-plugin-${UFM_HELM_VERSION}.tgz" "${ARTIFACT_PATH}/ufm-plugin-${UFM_HELM_VERSION}-helm.tgz"
echo "  Created: ${ARTIFACT_PATH}/ufm-plugin-${UFM_HELM_VERSION}-helm.tgz"
echo "========================================="
echo "SUCCESS: ufm-plugin-${UFM_HELM_VERSION}-helm.tgz"
echo "========================================="
