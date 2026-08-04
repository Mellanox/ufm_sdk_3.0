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
#   ufm-state-mirror/.ci/release_build.sh <VERSION> <RELEASE_ROOT> [RELEASE_ROOT_ALIAS]

set -eEo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
COMPONENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

VERSION="$1"
RELEASE_ROOT="$2"
RELEASE_ROOT_ALIAS="${3:-}"
IMAGE_NAME="ufm-state-mirror"
STAGING_DIR=""
STAGED_ARTIFACT=""
LATEST_TMP=""
LATEST_TMP_DIR=""
LATEST_LINK=""
LATEST_TARGET=""
PENDING_MARKER=""
WRITE_PROBE=""
BASE_DIR_CREATED=false
PENDING_MARKER_CREATED_BY_RUN=false
ARTIFACT_MOVE_ATTEMPTED=false
LATEST_MOVE_ATTEMPTED=false
LATEST_COMMITTED=false
BASE_VERSION_PATTERN='(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
VERSION_PATTERN='(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-([1-9][0-9]*))?'
RELEASE_GROUP_ID="${STATE_MIRROR_RELEASE_GROUP_ID:-4200}"

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
if [ -n "${RELEASE_ROOT_ALIAS}" ]; then
    if [[ "${RELEASE_ROOT_ALIAS}" != /* ]] || [ "${RELEASE_ROOT_ALIAS}" = "/" ]; then
        echo -e "Error: release-root alias must be an absolute path other than /."
        echo -e "Path: ${RELEASE_ROOT_ALIAS}"
        exit 1
    fi
    while [[ "${RELEASE_ROOT_ALIAS}" == */ ]]; do
        RELEASE_ROOT_ALIAS="${RELEASE_ROOT_ALIAS%/}"
    done
fi

BASE_VERSION=""
BUILD_NUMBER=""
# shellcheck disable=SC1091
source "${COMPONENT_DIR}/VERSION"

if [[ ! "${BASE_VERSION}" =~ ^${BASE_VERSION_PATTERN}$ ]]; then
    echo -e "Error: BASE_VERSION must use numeric MAJOR.MINOR.PATCH format."
    echo -e "BASE_VERSION: ${BASE_VERSION}"
    exit 1
fi
if [[ ! "${BUILD_NUMBER}" =~ ^([1-9][0-9]*)$ ]]; then
    echo -e "Error: BUILD_NUMBER must be a positive integer."
    echo -e "BASE_VERSION: ${BASE_VERSION}"
    echo -e "BUILD_NUMBER: ${BUILD_NUMBER}"
    exit 1
fi
EXTENDED_VERSION="${BASE_VERSION}-${BUILD_NUMBER}"
if [ "${VERSION}" != "${EXTENDED_VERSION}" ]; then
    echo -e "Error: ufm-state-mirror release version must match ufm-state-mirror/VERSION."
    echo -e "PLUGIN_VERSION: ${VERSION}"
    echo -e "Expected: ${EXTENDED_VERSION}"
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

normalize_version_directory_mode() {
    local directory="$1"
    local current_gid current_mode directory_details final_gid final_mode

    current_gid="$(stat -c '%g' "${directory}")"
    current_mode="$(stat -c '%a' "${directory}")"
    if [ "${current_gid}" = "${RELEASE_GROUP_ID}" ] && [ "${current_mode}" = 2775 ]; then
        return
    fi
    if { [ "${current_gid}" != "${RELEASE_GROUP_ID}" ] &&
         ! chgrp "${RELEASE_GROUP_ID}" "${directory}"; } ||
       ! chmod u=rwx,g=rwx,o=rx "${directory}" ||
       ! chmod u-s,g-s,o-t "${directory}" ||
       ! chmod g+s "${directory}"; then
        directory_details="$(stat -c 'owner=%U(%u) group=%G(%g) mode=%a' "${directory}")"
        echo -e "Error: base-version directory permissions cannot be normalized."
        echo -e "Path: ${directory}"
        echo -e "Current: ${directory_details}"
        echo -e "Expected: group GID ${RELEASE_GROUP_ID}, mode 2775"
        return 1
    fi
    final_gid="$(stat -c '%g' "${directory}")"
    final_mode="$(stat -c '%a' "${directory}")"
    if [ "${final_gid}" != "${RELEASE_GROUP_ID}" ] || [ "${final_mode}" != 2775 ]; then
        directory_details="$(stat -c 'owner=%U(%u) group=%G(%g) mode=%a' "${directory}")"
        echo -e "Error: base-version directory normalization did not reach the required state."
        echo -e "Path: ${directory}"
        echo -e "Current: ${directory_details}"
        echo -e "Expected: group GID ${RELEASE_GROUP_ID}, mode 2775"
        return 1
    fi
}

verify_version_directory_writable() {
    local directory="$1"
    local directory_details

    WRITE_PROBE=""
    if ! WRITE_PROBE="$(mktemp "${directory}/.write-test.XXXXXX")"; then
        directory_details="$(stat -c 'owner=%U(%u) group=%G(%g) mode=%a' "${directory}")"
        echo -e "Error: release process cannot write to the base-version directory."
        echo -e "Path: ${directory}"
        echo -e "Current: ${directory_details}"
        echo -e "Process: uid=$(id -u) gid=$(id -g)"
        echo -e "Expected: process group GID ${RELEASE_GROUP_ID}, directory mode=2775"
        return 1
    fi
    if ! rm -f -- "${WRITE_PROBE}"; then
        echo -e "Error: release process cannot remove its base-version write probe."
        echo -e "Path: ${WRITE_PROBE}"
        return 1
    fi
    WRITE_PROBE=""
}

latest_target_version() {
    local target="$1"
    local relative_target target_dir artifact version base_version expected_artifact

    if [[ "${target}" == "${RELEASE_ROOT}/"* ]]; then
        relative_target="${target#"${RELEASE_ROOT}/"}"
    elif [ -n "${RELEASE_ROOT_ALIAS}" ] &&
         [[ "${target}" == "${RELEASE_ROOT_ALIAS}/"* ]]; then
        relative_target="${target#"${RELEASE_ROOT_ALIAS}/"}"
    elif [[ "${target}" == "${PHYSICAL_RELEASE_ROOT}/"* ]]; then
        relative_target="${target#"${PHYSICAL_RELEASE_ROOT}/"}"
    elif [[ "${target}" == /* ]]; then
        return 1
    else
        relative_target="${target}"
    fi

    target_dir="${relative_target%%/*}"
    artifact="${relative_target#*/}"
    if [ "${artifact}" = "${relative_target}" ]; then
        return 1
    fi
    version="${artifact#"${IMAGE_NAME}_"}"
    version="${version%-docker.img.gz}"
    if [[ ! "${version}" =~ ^${VERSION_PATTERN}$ ]]; then
        return 1
    fi
    base_version="${version%%-*}"
    expected_artifact="${IMAGE_NAME}_${version}-docker.img.gz"
    if [ "${artifact}" != "${expected_artifact}" ] ||
       { [ "${target_dir}" != "${base_version}" ] && [ "${target_dir}" != "${version}" ]; }; then
        return 1
    fi
    printf '%s\n' "${version}"
}

cleanup_legacy_rollback_entries() {
    local entry unexpected_entry

    while IFS= read -r entry; do
        if [ -L "${entry}" ]; then
            if ! rm -f -- "${entry}"; then
                echo -e "Warning: cannot remove inaccessible legacy latest rollback entry."
                echo -e "Path: ${entry}"
                continue
            fi
        elif [ -d "${entry}" ]; then
            if [ ! -r "${entry}" ] || [ ! -x "${entry}" ]; then
                echo -e "Warning: cannot inspect inaccessible legacy latest rollback entry; ignoring it."
                echo -e "Path: ${entry}"
                continue
            fi
            if ! unexpected_entry="$(find "${entry}" -mindepth 1 -maxdepth 1 \
                ! -name latest -print -quit 2>/dev/null)"; then
                echo -e "Warning: cannot inspect inaccessible legacy latest rollback entry; ignoring it."
                echo -e "Path: ${entry}"
                continue
            fi
            if [ -n "${unexpected_entry}" ] ||
               { [ -e "${entry}/latest" ] && [ ! -L "${entry}/latest" ]; }; then
                echo -e "Error: legacy latest rollback entry contains unexpected data."
                echo -e "Path: ${entry}"
                exit 1
            fi
            if ! rm -f -- "${entry}/latest" || ! rmdir -- "${entry}"; then
                echo -e "Warning: cannot remove inaccessible legacy latest rollback entry."
                echo -e "Path: ${entry}"
                continue
            fi
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
    if [ "${LATEST_COMMITTED}" = false ] && [ "${LATEST_MOVE_ATTEMPTED}" = true ] &&
       [ -n "${LATEST_LINK}" ] &&
       [ -n "${LATEST_TARGET}" ] && [ -L "${LATEST_LINK}" ] &&
       [ "$(readlink "${LATEST_LINK}")" = "${LATEST_TARGET}" ]; then
        LATEST_COMMITTED=true
    fi
    if [ -n "${LATEST_TMP}" ]; then
        rm -f -- "${LATEST_TMP}"
    fi
    if [ -n "${LATEST_TMP_DIR}" ]; then
        rmdir -- "${LATEST_TMP_DIR}" 2>/dev/null || true
    fi
    if [ -n "${WRITE_PROBE}" ]; then
        rm -f -- "${WRITE_PROBE}" 2>/dev/null || true
    fi
    if [ "${LATEST_COMMITTED}" = false ] && [ "${ARTIFACT_MOVE_ATTEMPTED}" = true ] &&
       [ ! -e "${STAGED_ARTIFACT}" ] && [ ! -L "${STAGED_ARTIFACT}" ]; then
        rm -f -- "${ARTIFACT_PATH}"
    fi
    if [ -n "${STAGING_DIR}" ]; then
        rm -rf -- "${STAGING_DIR}"
    fi
    if [ "${LATEST_COMMITTED}" = false ] && [ "${PENDING_MARKER_CREATED_BY_RUN}" = true ]; then
        rm -f -- "${PENDING_MARKER}"
    fi
    if [ "${BASE_DIR_CREATED}" = true ] && [ "${LATEST_COMMITTED}" = false ]; then
        rmdir -- "${BASE_VERSION_DIR}" 2>/dev/null || true
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

BASE_VERSION_DIR="${RELEASE_ROOT}/${BASE_VERSION}"
ARTIFACT_NAME="${IMAGE_NAME}_${VERSION}-docker.img.gz"
ARTIFACT_PATH="${BASE_VERSION_DIR}/${ARTIFACT_NAME}"
LEGACY_VERSION_DIR="${RELEASE_ROOT}/${VERSION}"
LEGACY_ARTIFACT_PATH="${LEGACY_VERSION_DIR}/${ARTIFACT_NAME}"
LATEST_LINK="${RELEASE_ROOT}/latest"
LATEST_TARGET="${ARTIFACT_PATH}"
PENDING_MARKER="${BASE_VERSION_DIR}/.${VERSION}.pending-latest"
RESUME_PUBLISH=false

if [ -L "${BASE_VERSION_DIR}" ] || { [ -e "${BASE_VERSION_DIR}" ] && [ ! -d "${BASE_VERSION_DIR}" ]; }; then
    echo -e "Error: base version path exists and is not a directory."
    echo -e "Path: ${BASE_VERSION_DIR}"
    exit 1
fi
if [ ! -d "${BASE_VERSION_DIR}" ]; then
    mkdir "${BASE_VERSION_DIR}"
    BASE_DIR_CREATED=true
fi
normalize_version_directory_mode "${BASE_VERSION_DIR}"

if [ "${LEGACY_VERSION_DIR}" != "${BASE_VERSION_DIR}" ] &&
   { [ -e "${LEGACY_ARTIFACT_PATH}" ] || [ -L "${LEGACY_ARTIFACT_PATH}" ]; }; then
    echo -e "A legacy flat build for ${IMAGE_NAME} ${VERSION} already exists."
    echo -e "Path: ${LEGACY_ARTIFACT_PATH}"
    exit 1
fi

if [ -e "${PENDING_MARKER}" ] || [ -L "${PENDING_MARKER}" ]; then
    if [ -f "${PENDING_MARKER}" ] && [ ! -L "${PENDING_MARKER}" ]; then
        if release_artifact_is_valid "${BASE_VERSION_DIR}" "${ARTIFACT_PATH}"; then
            echo "Resuming latest publication for ${IMAGE_NAME} ${VERSION}."
            RESUME_PUBLISH=true
        elif [ -L "${LATEST_LINK}" ] && [ "$(readlink "${LATEST_LINK}")" = "${LATEST_TARGET}" ]; then
            echo -e "Error: latest points to an invalid incomplete release."
            echo -e "Path: ${ARTIFACT_PATH}"
            exit 1
        else
            rm -f -- "${ARTIFACT_PATH}" "${PENDING_MARKER}"
        fi
    else
        echo -e "Error: pending release marker has an unexpected type."
        echo -e "Path: ${PENDING_MARKER}"
        exit 1
    fi
elif [ -e "${ARTIFACT_PATH}" ] || [ -L "${ARTIFACT_PATH}" ]; then
    echo -e "A build for ${IMAGE_NAME} ${VERSION} already exists."
    echo -e "Path: ${ARTIFACT_PATH}"
    exit 1
fi

if [ -L "${LATEST_LINK}" ]; then
    CURRENT_TARGET="$(readlink "${LATEST_LINK}")"
    if ! CURRENT_VERSION="$(latest_target_version "${CURRENT_TARGET}")"; then
        echo -e "Error: ${LATEST_LINK} has an unexpected target."
        echo -e "Target: ${CURRENT_TARGET}"
        exit 1
    fi
    CURRENT_BASE_VERSION="${CURRENT_VERSION%%-*}"
    EXPECTED_CURRENT_TARGET="${RELEASE_ROOT}/${CURRENT_BASE_VERSION}/${IMAGE_NAME}_${CURRENT_VERSION}-docker.img.gz"
    CURRENT_VERSION_DIR="${RELEASE_ROOT}/${CURRENT_BASE_VERSION}"
    CURRENT_ARTIFACT="${EXPECTED_CURRENT_TARGET}"
    if version_is_older "${VERSION}" "${CURRENT_VERSION}"; then
        if [ "${RESUME_PUBLISH}" = true ]; then
            rm -f -- "${PENDING_MARKER}"
        fi
        echo -e "Error: refusing to move latest from ${CURRENT_VERSION} back to ${VERSION}."
        exit 1
    fi
    if [ "${VERSION}" = "${CURRENT_VERSION}" ] && [ "${RESUME_PUBLISH}" = false ]; then
        echo -e "Error: refusing to rebuild immutable version ${VERSION} from a stale latest target."
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

verify_version_directory_writable "${BASE_VERSION_DIR}"

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
    PENDING_MARKER_CREATED_BY_RUN=true
    touch "${PENDING_MARKER}"
    ARTIFACT_MOVE_ATTEMPTED=true
    mv -T "${STAGED_ARTIFACT}" "${ARTIFACT_PATH}"
    rmdir -- "${STAGING_DIR}"
    STAGING_DIR=""
fi

if [ "${RESUME_PUBLISH}" = true ]; then
    chmod 0644 "${ARTIFACT_PATH}"
    normalize_version_directory_mode "${BASE_VERSION_DIR}"
fi

LATEST_TMP_DIR="$(mktemp -d "${RELEASE_ROOT}/.latest.staging.XXXXXX")"
LATEST_TMP="${LATEST_TMP_DIR}/latest"
ln -s "${LATEST_TARGET}" "${LATEST_TMP}"
LATEST_MOVE_ATTEMPTED=true
mv -Tf "${LATEST_TMP}" "${LATEST_LINK}"
LATEST_TMP=""
LATEST_COMMITTED=true
rmdir -- "${LATEST_TMP_DIR}"
LATEST_TMP_DIR=""
rm -f -- "${PENDING_MARKER}"

echo "Updated ${RELEASE_ROOT}/latest -> ${LATEST_TARGET}"
