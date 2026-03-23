#!/bin/bash
# Package the ufm-plugins Helm chart.
# Usage: do_create_ufm_plugin_helm_chart.sh <UFM_HELM_VERSION> [ARTIFACT_PATH]
set -e

UFM_HELM_VERSION="${1}"
ARTIFACT_PATH="${2:-/tmp/ufm-plugin-helm}"

if [ -z "${UFM_HELM_VERSION}" ]; then
    echo "ERROR: UFM_HELM_VERSION is required"
    echo "Usage: $0 <UFM_HELM_VERSION> [ARTIFACT_PATH]"
    exit 1
fi

if [ -z "${WORKSPACE}" ]; then
    WORKSPACE=$(pwd)
    export WORKSPACE
fi

CHART_DIR="${WORKSPACE}/ufm-plugin-helm-template"

echo "========================================="
echo "Creating UFM Plugin Helm Chart"
echo "========================================="
echo "Version: ${UFM_HELM_VERSION}"
echo "Chart:   ${CHART_DIR}"
echo "Output:  ${ARTIFACT_PATH}"
echo "========================================="

if [ ! -d "${CHART_DIR}" ]; then
    echo "ERROR: ufm-plugins chart not found at ${CHART_DIR}"
    exit 1
fi

if ! command -v helm &>/dev/null; then
    echo "Installing Helm..."
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

echo ""
echo "Step 1: Validating chart..."
helm lint "${CHART_DIR}"

echo ""
echo "Step 2: Packaging chart..."
mkdir -p "${ARTIFACT_PATH}"
helm package "${CHART_DIR}" \
    --version "${UFM_HELM_VERSION}" \
    --app-version "${UFM_HELM_VERSION}" \
    --destination "${ARTIFACT_PATH}"

CHART_NAME=$(grep '^name:' "${CHART_DIR}/Chart.yaml" | awk '{print $2}')
CHART_FILE="${CHART_NAME}-${UFM_HELM_VERSION}.tgz"
ARTIFACT_FILE="${CHART_NAME}-${UFM_HELM_VERSION}-helm.tgz"

if [ -f "${ARTIFACT_PATH}/${CHART_FILE}" ]; then
    mv "${ARTIFACT_PATH}/${CHART_FILE}" "${ARTIFACT_PATH}/${ARTIFACT_FILE}"
fi

echo ""
echo "========================================="
echo "SUCCESS: ${ARTIFACT_FILE}"
echo "Location: ${ARTIFACT_PATH}/"
echo "========================================="
