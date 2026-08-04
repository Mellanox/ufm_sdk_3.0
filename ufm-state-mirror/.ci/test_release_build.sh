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

set -eEuo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
TEST_ROOT="$(mktemp -d /tmp/ufm-state-mirror-release-test.XXXXXX)"
TEST_ROOT="$(cd "${TEST_ROOT}" && pwd -P)"
trap 'rm -rf -- "${TEST_ROOT}"' EXIT

make_component() {
    local name="$1"
    local base_version="$2"
    local extended_version="$3"
    local component_dir="${TEST_ROOT}/${name}"

    cp -R "${SOURCE_DIR}" "${component_dir}"
    printf 'BASE_VERSION=%s\nEXTENDED_VERSION=%s\n' \
        "${base_version}" "${extended_version}" > "${component_dir}/VERSION"
    cat > "${component_dir}/build/docker_build.sh" <<'STUB'
#!/bin/bash
set -eEuo pipefail
version="$1"
output_dir="$2"
mkdir -p "${output_dir}"
printf 'release fixture\n' | gzip > "${output_dir}/ufm-state-mirror_${version}-docker.img.gz"
STUB
    chmod +x "${component_dir}/build/docker_build.sh"
    printf '%s\n' "${component_dir}"
}

make_artifact() {
    local release_root="$1"
    local version="$2"
    local base_version="${version%%-*}"
    local version_dir="${release_root}/${base_version}"

    mkdir -p "${version_dir}"
    printf 'existing release fixture\n' |
        gzip > "${version_dir}/ufm-state-mirror_${version}-docker.img.gz"
}

make_legacy_flat_artifact() {
    local release_root="$1"
    local version="$2"
    local version_dir="${release_root}/${version}"

    mkdir -p "${version_dir}"
    printf 'legacy release fixture\n' |
        gzip > "${version_dir}/ufm-state-mirror_${version}-docker.img.gz"
}

run_release() {
    local component_dir="$1"
    local version="$2"
    local release_root="$3"
    local release_root_alias="${4:-}"

    "${component_dir}/.ci/release_build.sh" \
        "${version}" "${release_root}" "${release_root_alias}"
}

assert_link_target() {
    local link="$1"
    local expected="$2"
    local actual

    actual="$(readlink "${link}")"
    if [ "${actual}" != "${expected}" ]; then
        echo "Expected ${link} -> ${expected}, got ${actual}" >&2
        exit 1
    fi
}

PHYSICAL_ROOT="${TEST_ROOT}/physical-release"
LOGICAL_ROOT="${TEST_ROOT}/logical-release"
mkdir -p "${PHYSICAL_ROOT}"
ln -s "${PHYSICAL_ROOT}" "${LOGICAL_ROOT}"

make_artifact "${PHYSICAL_ROOT}" "1.0.1"
chmod 0777 "${PHYSICAL_ROOT}/1.0.1"
ln -s "1.0.1/ufm-state-mirror_1.0.1-docker.img.gz" "${PHYSICAL_ROOT}/latest"
mkdir "${PHYSICAL_ROOT}/.latest.rollback.fixture"
ln -s "1.0.1/ufm-state-mirror_1.0.1-docker.img.gz" \
    "${PHYSICAL_ROOT}/.latest.rollback.fixture/latest"

COMPONENT_8="$(make_component component-8 1.0.1 1.0.1-8)"
run_release "${COMPONENT_8}" "1.0.1-8" "${LOGICAL_ROOT}"
assert_link_target "${PHYSICAL_ROOT}/latest" \
    "${LOGICAL_ROOT}/1.0.1/ufm-state-mirror_1.0.1-8-docker.img.gz"
test ! -e "${PHYSICAL_ROOT}/.latest.rollback.fixture"
test ! -e "${PHYSICAL_ROOT}/1.0.1-8"
test -f "${PHYSICAL_ROOT}/1.0.1/ufm-state-mirror_1.0.1-docker.img.gz"
test "$(stat -c '%a' "${PHYSICAL_ROOT}/1.0.1")" = 755
test "$(stat -c '%a' "${PHYSICAL_ROOT}/1.0.1/ufm-state-mirror_1.0.1-8-docker.img.gz")" = 644

rm -f "${PHYSICAL_ROOT}/latest"
make_legacy_flat_artifact "${PHYSICAL_ROOT}" "1.0.1-8"
ln -s "${PHYSICAL_ROOT}/1.0.1-8/ufm-state-mirror_1.0.1-8-docker.img.gz" \
    "${PHYSICAL_ROOT}/latest"
COMPONENT_9="$(make_component component-9 1.0.1 1.0.1-9)"
run_release "${COMPONENT_9}" "1.0.1-9" "${LOGICAL_ROOT}"
assert_link_target "${PHYSICAL_ROOT}/latest" \
    "${LOGICAL_ROOT}/1.0.1/ufm-state-mirror_1.0.1-9-docker.img.gz"
test -f "${PHYSICAL_ROOT}/1.0.1/ufm-state-mirror_1.0.1-8-docker.img.gz"
test -f "${PHYSICAL_ROOT}/1.0.1/ufm-state-mirror_1.0.1-9-docker.img.gz"

rm -f "${PHYSICAL_ROOT}/latest"
ln -s "1.0.1/ufm-state-mirror_1.0.1-9-docker.img.gz" "${PHYSICAL_ROOT}/latest"
rm -f "${PHYSICAL_ROOT}/1.0.1/ufm-state-mirror_1.0.1-9-docker.img.gz"
COMPONENT_10="$(make_component component-10 1.0.1 1.0.1-10)"
run_release "${COMPONENT_10}" "1.0.1-10" "${LOGICAL_ROOT}"
assert_link_target "${PHYSICAL_ROOT}/latest" \
    "${LOGICAL_ROOT}/1.0.1/ufm-state-mirror_1.0.1-10-docker.img.gz"

if run_release "${COMPONENT_10}" "1.0.1-10" "${LOGICAL_ROOT}"; then
    echo "Expected duplicate extended-version publication rejection" >&2
    exit 1
fi
test -f "${PHYSICAL_ROOT}/1.0.1/ufm-state-mirror_1.0.1-8-docker.img.gz"
test -f "${PHYSICAL_ROOT}/1.0.1/ufm-state-mirror_1.0.1-10-docker.img.gz"

RESUME_ROOT="${TEST_ROOT}/resume-release"
make_artifact "${RESUME_ROOT}" "1.0.3-4"
touch "${RESUME_ROOT}/1.0.3/.1.0.3-4.pending-latest"
COMPONENT_RESUME="$(make_component component-resume 1.0.3 1.0.3-4)"
printf '#!/bin/bash\nexit 99\n' > "${COMPONENT_RESUME}/build/docker_build.sh"
chmod +x "${COMPONENT_RESUME}/build/docker_build.sh"
run_release "${COMPONENT_RESUME}" "1.0.3-4" "${RESUME_ROOT}"
assert_link_target "${RESUME_ROOT}/latest" \
    "${RESUME_ROOT}/1.0.3/ufm-state-mirror_1.0.3-4-docker.img.gz"
test ! -e "${RESUME_ROOT}/1.0.3/.1.0.3-4.pending-latest"

SIGNAL_ROOT="${TEST_ROOT}/signal-release"
SIGNAL_COMPONENT="$(make_component component-signal 1.0.5 1.0.5-1)"
SIGNAL_BIN="${TEST_ROOT}/signal-bin"
SIGNAL_REAL_MV="$(command -v mv)"
mkdir -p "${SIGNAL_BIN}"
cat > "${SIGNAL_BIN}/mv" <<'SIGNAL_MV'
#!/bin/bash
set -eEuo pipefail
destination="${!#}"
"${SIGNAL_REAL_MV}" "$@"
if [[ "${destination}" == */latest ]]; then
    kill -TERM "${PPID}"
fi
SIGNAL_MV
chmod +x "${SIGNAL_BIN}/mv"
if (
    export SIGNAL_REAL_MV
    export PATH="${SIGNAL_BIN}:${PATH}"
    run_release "${SIGNAL_COMPONENT}" "1.0.5-1" "${SIGNAL_ROOT}"
); then
    echo "Expected injected post-latest SIGTERM to interrupt publication" >&2
    exit 1
fi
assert_link_target "${SIGNAL_ROOT}/latest" \
    "${SIGNAL_ROOT}/1.0.5/ufm-state-mirror_1.0.5-1-docker.img.gz"
test -f "${SIGNAL_ROOT}/1.0.5/ufm-state-mirror_1.0.5-1-docker.img.gz"
test -f "${SIGNAL_ROOT}/1.0.5/.1.0.5-1.pending-latest"
run_release "${SIGNAL_COMPONENT}" "1.0.5-1" "${SIGNAL_ROOT}"
test ! -e "${SIGNAL_ROOT}/1.0.5/.1.0.5-1.pending-latest"

DOWNGRADE_PHYSICAL_ROOT="${TEST_ROOT}/downgrade-physical"
DOWNGRADE_LOGICAL_ROOT="${TEST_ROOT}/downgrade-logical"
mkdir -p "${DOWNGRADE_PHYSICAL_ROOT}"
ln -s "${DOWNGRADE_PHYSICAL_ROOT}" "${DOWNGRADE_LOGICAL_ROOT}"
ln -s "${DOWNGRADE_PHYSICAL_ROOT}/1.0.2/ufm-state-mirror_1.0.2-1-docker.img.gz" \
    "${DOWNGRADE_PHYSICAL_ROOT}/latest"
COMPONENT_99="$(make_component component-99 1.0.1 1.0.1-99)"
if run_release "${COMPONENT_99}" "1.0.1-99" "${DOWNGRADE_LOGICAL_ROOT}"; then
    echo "Expected build-suffix downgrade rejection" >&2
    exit 1
fi

SAME_CORE_ROOT="${TEST_ROOT}/same-core-release"
mkdir -p "${SAME_CORE_ROOT}"
make_artifact "${SAME_CORE_ROOT}" "1.0.1-10"
ln -s "${SAME_CORE_ROOT}/1.0.1/ufm-state-mirror_1.0.1-10-docker.img.gz" \
    "${SAME_CORE_ROOT}/latest"
COMPONENT_9_DOWNGRADE="$(make_component component-9-downgrade 1.0.1 1.0.1-9)"
if run_release "${COMPONENT_9_DOWNGRADE}" "1.0.1-9" "${SAME_CORE_ROOT}"; then
    echo "Expected same-core build-suffix downgrade rejection" >&2
    exit 1
fi

UNSAFE_ROLLBACK_ROOT="${TEST_ROOT}/unsafe-rollback-release"
mkdir -p "${UNSAFE_ROLLBACK_ROOT}/.latest.rollback.fixture"
printf 'must be preserved\n' > \
    "${UNSAFE_ROLLBACK_ROOT}/.latest.rollback.fixture/unexpected-data"
COMPONENT_UNSAFE="$(make_component component-unsafe 1.0.1 1.0.1-11)"
if run_release "${COMPONENT_UNSAFE}" "1.0.1-11" "${UNSAFE_ROLLBACK_ROOT}"; then
    echo "Expected unsafe legacy rollback cleanup rejection" >&2
    exit 1
fi
test -f "${UNSAFE_ROLLBACK_ROOT}/.latest.rollback.fixture/unexpected-data"

COMPONENT_INVALID="$(make_component component-invalid 1.0.1 1.0.1-0)"
if run_release "${COMPONENT_INVALID}" "1.0.1-0" "${TEST_ROOT}/invalid-release"; then
    echo "Expected build suffix 0 to be rejected" >&2
    exit 1
fi

COMPONENT_MISMATCH="$(make_component component-mismatch 1.0.2 1.0.1-12)"
if run_release "${COMPONENT_MISMATCH}" "1.0.1-12" "${TEST_ROOT}/mismatch-release"; then
    echo "Expected mismatched base and extended versions to be rejected" >&2
    exit 1
fi

COMPONENT_MALFORMED="$(make_component component-malformed 1.0.1 1x0y1-8)"
if run_release "${COMPONENT_MALFORMED}" "1x0y1-8" "${TEST_ROOT}/malformed-release"; then
    echo "Expected malformed extended version to be rejected" >&2
    exit 1
fi

STALE_PENDING_ROOT="${TEST_ROOT}/stale-pending-release"
make_artifact "${STALE_PENDING_ROOT}" "1.0.1-8"
make_artifact "${STALE_PENDING_ROOT}" "1.0.1-9"
touch "${STALE_PENDING_ROOT}/1.0.1/.1.0.1-8.pending-latest"
ln -s "${STALE_PENDING_ROOT}/1.0.1/ufm-state-mirror_1.0.1-9-docker.img.gz" \
    "${STALE_PENDING_ROOT}/latest"
COMPONENT_STALE="$(make_component component-stale 1.0.1 1.0.1-8)"
if run_release "${COMPONENT_STALE}" "1.0.1-8" "${STALE_PENDING_ROOT}"; then
    echo "Expected resumed older build to be rejected" >&2
    exit 1
fi
test -f "${STALE_PENDING_ROOT}/1.0.1/ufm-state-mirror_1.0.1-8-docker.img.gz"
test -f "${STALE_PENDING_ROOT}/1.0.1/ufm-state-mirror_1.0.1-9-docker.img.gz"
test ! -e "${STALE_PENDING_ROOT}/1.0.1/.1.0.1-8.pending-latest"
assert_link_target "${STALE_PENDING_ROOT}/latest" \
    "${STALE_PENDING_ROOT}/1.0.1/ufm-state-mirror_1.0.1-9-docker.img.gz"

FAILED_RESUME_ROOT="${TEST_ROOT}/failed-resume-release"
make_artifact "${FAILED_RESUME_ROOT}" "1.0.4-1"
touch "${FAILED_RESUME_ROOT}/1.0.4/.1.0.4-1.pending-latest"
ln -s "/unexpected/latest-target" "${FAILED_RESUME_ROOT}/latest"
COMPONENT_FAILED_RESUME="$(make_component component-failed-resume 1.0.4 1.0.4-1)"
if run_release "${COMPONENT_FAILED_RESUME}" "1.0.4-1" "${FAILED_RESUME_ROOT}"; then
    echo "Expected recovery with an unexpected latest target to fail" >&2
    exit 1
fi
test -f "${FAILED_RESUME_ROOT}/1.0.4/ufm-state-mirror_1.0.4-1-docker.img.gz"
test -f "${FAILED_RESUME_ROOT}/1.0.4/.1.0.4-1.pending-latest"
assert_link_target "${FAILED_RESUME_ROOT}/latest" "/unexpected/latest-target"

EQUAL_STALE_ROOT="${TEST_ROOT}/equal-stale-release"
mkdir -p "${EQUAL_STALE_ROOT}"
ln -s "${EQUAL_STALE_ROOT}/1.0.7/ufm-state-mirror_1.0.7-1-docker.img.gz" \
    "${EQUAL_STALE_ROOT}/latest"
COMPONENT_EQUAL_STALE="$(make_component component-equal-stale 1.0.7 1.0.7-1)"
if run_release "${COMPONENT_EQUAL_STALE}" "1.0.7-1" "${EQUAL_STALE_ROOT}"; then
    echo "Expected equal-version dangling latest to reject immutable rebuild" >&2
    exit 1
fi
test ! -e "${EQUAL_STALE_ROOT}/1.0.7/ufm-state-mirror_1.0.7-1-docker.img.gz"
assert_link_target "${EQUAL_STALE_ROOT}/latest" \
    "${EQUAL_STALE_ROOT}/1.0.7/ufm-state-mirror_1.0.7-1-docker.img.gz"

EXPLICIT_ALIAS_ROOT="${TEST_ROOT}/explicit-alias-release"
EXPLICIT_ALIAS="${TEST_ROOT}/unresolved-physical-alias"
make_artifact "${EXPLICIT_ALIAS_ROOT}" "1.0.8-1"
ln -s "${EXPLICIT_ALIAS}/1.0.8/ufm-state-mirror_1.0.8-1-docker.img.gz" \
    "${EXPLICIT_ALIAS_ROOT}/latest"
COMPONENT_ALIAS="$(make_component component-alias 1.0.8 1.0.8-2)"
run_release "${COMPONENT_ALIAS}" "1.0.8-2" \
    "${EXPLICIT_ALIAS_ROOT}" "${EXPLICIT_ALIAS}"
assert_link_target "${EXPLICIT_ALIAS_ROOT}/latest" \
    "${EXPLICIT_ALIAS_ROOT}/1.0.8/ufm-state-mirror_1.0.8-2-docker.img.gz"

echo "StateMirror release helper tests passed"
