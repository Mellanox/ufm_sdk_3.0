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
#   ufm-state-mirror/.ci/release_build.sh <VERSION> <RELEASE_ROOT>

set -eEo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
COMPONENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

VERSION="$1"
RELEASE_ROOT="$2"
IMAGE_NAME="ufm-state-mirror"
STAGING_DIR=""
LATEST_TMP=""
LATEST_TMP_DIR=""
VERSION_PUBLISHED=false
LATEST_COMMITTED=false
VERSION_PATTERN='(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-([1-9][0-9]*))?'

if [ -z "${VERSION}" ] || [ -z "${RELEASE_ROOT}" ]; then
    echo "Usage: $0 <VERSION> <RELEASE_ROOT>"
    exit 2
fi

if [[ "${RELEASE_ROOT}" != /* ]] || [ "${RELEASE_ROOT}" = "/" ]; then
    echo -e "Error: release root must be an absolute path other than /."
    echo -e "Path: ${RELEASE_ROOT}"
    exit 1
fi
while [[ "${RELEASE_ROOT}" == */ ]]; do
    RELEASE_ROOT="${RELEASE_ROOT%/}"
done

EXPECTED_VERSION="$(tr -d '\n' < "${COMPONENT_DIR}/VERSION")"
if [ "${VERSION}" != "${EXPECTED_VERSION}" ]; then
    echo -e "Error: ufm-state-mirror release version must match ufm-state-mirror/VERSION."
    echo -e "PLUGIN_VERSION: ${VERSION}"
    echo -e "Expected: ${EXPECTED_VERSION}"
    exit 1
fi

if [[ ! "${VERSION}" =~ ^${VERSION_PATTERN}$ ]]; then
    echo -e "Error: release version must use MAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH-BUILD format."
    echo -e "Version: ${VERSION}"
    exit 1
fi

version_is_older() {
    local candidate_core candidate_major candidate_minor candidate_patch candidate_build
    local current_core current_major current_minor current_patch current_build

    candidate_core="${1%%-*}"
    current_core="${2%%-*}"
    candidate_build=0
    current_build=0
    if [[ "$1" == *-* ]]; then
        candidate_build="${1##*-}"
    fi
    if [[ "$2" == *-* ]]; then
        current_build="${2##*-}"
    fi

    IFS=. read -r candidate_major candidate_minor candidate_patch <<< "${candidate_core}"
    IFS=. read -r current_major current_minor current_patch <<< "${current_core}"

    if [ "${candidate_major}" != "${current_major}" ]; then
        numeric_component_is_older "${candidate_major}" "${current_major}"
        return
    fi
    if [ "${candidate_minor}" != "${current_minor}" ]; then
        numeric_component_is_older "${candidate_minor}" "${current_minor}"
        return
    fi
    if [ "${candidate_patch}" != "${current_patch}" ]; then
        numeric_component_is_older "${candidate_patch}" "${current_patch}"
        return
    fi
    if [ "${candidate_build}" != "${current_build}" ]; then
        numeric_component_is_older "${candidate_build}" "${current_build}"
        return
    fi
    return 1
}

numeric_component_is_older() {
    local candidate="$1"
    local current="$2"

    if [ "${#candidate}" -ne "${#current}" ]; then
        [ "${#candidate}" -lt "${#current}" ]
        return
    fi
    [[ "${candidate}" < "${current}" ]]
}

release_artifact_is_valid() {
    local version_dir="$1"
    local artifact="$2"

    [ -d "${version_dir}" ] &&
        [ ! -L "${version_dir}" ] &&
        [ -f "${artifact}" ] &&
        [ ! -L "${artifact}" ] &&
        [ -s "${artifact}" ] &&
        gzip -t "${artifact}"
}

latest_target_version() {
    local target="$1"
    local relative_target version expected_relative_target

    case "${target}" in
        "${RELEASE_ROOT}/"*)
            relative_target="${target#"${RELEASE_ROOT}/"}"
            ;;
        "${PHYSICAL_RELEASE_ROOT}/"*)
            relative_target="${target#"${PHYSICAL_RELEASE_ROOT}/"}"
            ;;
        /*)
            return 1
            ;;
        *)
            relative_target="${target}"
            ;;
    esac

    version="${relative_target%%/*}"
    if [[ ! "${version}" =~ ^${VERSION_PATTERN}$ ]]; then
        return 1
    fi
    expected_relative_target="${version}/${IMAGE_NAME}_${version}-docker.img.gz"
    if [ "${relative_target}" != "${expected_relative_target}" ]; then
        return 1
    fi
    printf '%s\n' "${version}"
}

cleanup_legacy_rollback_entries() {
    local entry unexpected_entry

    while IFS= read -r entry; do
        if [ -L "${entry}" ]; then
            rm -f -- "${entry}"
        elif [ -d "${entry}" ]; then
            unexpected_entry="$(find "${entry}" -mindepth 1 -maxdepth 1 ! -name latest -print -quit)"
            if [ -n "${unexpected_entry}" ] ||
               { [ -e "${entry}/latest" ] && [ ! -L "${entry}/latest" ]; }; then
                echo -e "Error: legacy latest rollback entry contains unexpected data."
                echo -e "Path: ${entry}"
                exit 1
            fi
            rm -f -- "${entry}/latest"
            rmdir -- "${entry}"
        else
            echo -e "Error: legacy latest rollback entry has an unexpected type."
            echo -e "Path: ${entry}"
            exit 1
        fi
        echo "Removed legacy latest rollback entry: ${entry}"
    done < <(find -H "${RELEASE_ROOT}" -mindepth 1 -maxdepth 1 \
        -name '.latest.rollback.*' -print)
}

cleanup() {
    if [ -n "${LATEST_TMP}" ]; then
        rm -f -- "${LATEST_TMP}"
    fi
    if [ -n "${LATEST_TMP_DIR}" ]; then
        rmdir -- "${LATEST_TMP_DIR}" 2>/dev/null || true
    fi
    if [ -n "${STAGING_DIR}" ]; then
        rm -rf -- "${STAGING_DIR}"
    fi
    if [ "${VERSION_PUBLISHED}" = true ] && [ "${LATEST_COMMITTED}" = false ]; then
        rm -rf -- "${VERSION_DIR}"
    fi
}
trap cleanup EXIT

mkdir -p "${RELEASE_ROOT}"
exec 9>"${RELEASE_ROOT}/.release.lock"
if ! flock -n 9; then
    echo -e "Error: another ${IMAGE_NAME} release is already in progress."
    echo -e "Lock: ${RELEASE_ROOT}/.release.lock"
    exit 1
fi
PHYSICAL_RELEASE_ROOT="$(cd "${RELEASE_ROOT}" && pwd -P)"
cleanup_legacy_rollback_entries

VERSION_DIR="${RELEASE_ROOT}/${VERSION}"
ARTIFACT_NAME="${IMAGE_NAME}_${VERSION}-docker.img.gz"
LATEST_LINK="${RELEASE_ROOT}/latest"
LATEST_TARGET="${VERSION_DIR}/${ARTIFACT_NAME}"
PENDING_MARKER="${VERSION_DIR}/.pending-latest"
RESUME_PUBLISH=false

if [ -e "${VERSION_DIR}" ] || [ -L "${VERSION_DIR}" ]; then
    if [ -f "${PENDING_MARKER}" ] && [ ! -L "${PENDING_MARKER}" ]; then
        UNEXPECTED_ENTRY="$(find "${VERSION_DIR}" -mindepth 1 -maxdepth 1 \
            ! -name "${ARTIFACT_NAME}" ! -name ".pending-latest" -print -quit)"
        if [ -n "${UNEXPECTED_ENTRY}" ]; then
            echo -e "Error: incomplete release directory contains an unexpected entry."
            echo -e "Path: ${UNEXPECTED_ENTRY}"
            exit 1
        fi
        if release_artifact_is_valid "${VERSION_DIR}" "${VERSION_DIR}/${ARTIFACT_NAME}"; then
            echo "Resuming latest publication for ${IMAGE_NAME} ${VERSION}."
            RESUME_PUBLISH=true
            VERSION_PUBLISHED=true
        elif [ -L "${LATEST_LINK}" ] && [ "$(readlink "${LATEST_LINK}")" = "${LATEST_TARGET}" ]; then
            echo -e "Error: latest points to an invalid incomplete release."
            echo -e "Path: ${VERSION_DIR}"
            exit 1
        else
            rm -rf -- "${VERSION_DIR}"
        fi
    else
        echo -e "A build for ${IMAGE_NAME} ${VERSION} already exists."
        echo -e "Path: ${VERSION_DIR}"
        exit 1
    fi
fi

if [ -L "${LATEST_LINK}" ]; then
    CURRENT_TARGET="$(readlink "${LATEST_LINK}")"
    if ! CURRENT_VERSION="$(latest_target_version "${CURRENT_TARGET}")"; then
        echo -e "Error: ${LATEST_LINK} has an unexpected target."
        echo -e "Target: ${CURRENT_TARGET}"
        exit 1
    fi
    EXPECTED_CURRENT_TARGET="${RELEASE_ROOT}/${CURRENT_VERSION}/${IMAGE_NAME}_${CURRENT_VERSION}-docker.img.gz"
    CURRENT_VERSION_DIR="${RELEASE_ROOT}/${CURRENT_VERSION}"
    CURRENT_ARTIFACT="${EXPECTED_CURRENT_TARGET}"
    if version_is_older "${VERSION}" "${CURRENT_VERSION}"; then
        echo -e "Error: refusing to move latest from ${CURRENT_VERSION} back to ${VERSION}."
        exit 1
    fi
    if ! release_artifact_is_valid "${CURRENT_VERSION_DIR}" "${CURRENT_ARTIFACT}"; then
        echo -e "Warning: ${LATEST_LINK} is stale or dangling and will be replaced after a successful release."
        echo -e "Target: ${CURRENT_TARGET}"
    elif [ "${CURRENT_TARGET}" != "${EXPECTED_CURRENT_TARGET}" ]; then
        echo "Migrating legacy latest target: ${CURRENT_TARGET}"
    fi
elif [ -e "${LATEST_LINK}" ]; then
    echo -e "Error: ${LATEST_LINK} exists and is not a symbolic link."
    exit 1
fi

if [ "${RESUME_PUBLISH}" = false ]; then
    STAGING_DIR="$(mktemp -d "${RELEASE_ROOT}/.${VERSION}.staging.XXXXXX")"
    cd "${COMPONENT_DIR}/build"
    bash -x ./docker_build.sh "${VERSION}" "${STAGING_DIR}"

    STAGED_ARTIFACT="${STAGING_DIR}/${ARTIFACT_NAME}"
    if ! release_artifact_is_valid "${STAGING_DIR}" "${STAGED_ARTIFACT}"; then
        echo -e "Error: expected release artifact was not created."
        echo -e "Path: ${STAGED_ARTIFACT}"
        exit 1
    fi

    chmod 0644 "${STAGED_ARTIFACT}"
    chmod u+rwx,go+rx "${STAGING_DIR}"
    touch "${STAGING_DIR}/.pending-latest"
    mv -T "${STAGING_DIR}" "${VERSION_DIR}"
    STAGING_DIR=""
    VERSION_PUBLISHED=true
fi

if [ "${RESUME_PUBLISH}" = true ]; then
    chmod 0644 "${VERSION_DIR}/${ARTIFACT_NAME}"
    chmod u+rwx,go+rx "${VERSION_DIR}"
fi

LATEST_TMP_DIR="$(mktemp -d "${RELEASE_ROOT}/.latest.staging.XXXXXX")"
LATEST_TMP="${LATEST_TMP_DIR}/latest"
ln -s "${LATEST_TARGET}" "${LATEST_TMP}"
mv -Tf "${LATEST_TMP}" "${LATEST_LINK}"
LATEST_TMP=""
LATEST_COMMITTED=true
rmdir -- "${LATEST_TMP_DIR}"
LATEST_TMP_DIR=""
rm -f -- "${PENDING_MARKER}"

echo "Updated ${RELEASE_ROOT}/latest -> ${LATEST_TARGET}"
