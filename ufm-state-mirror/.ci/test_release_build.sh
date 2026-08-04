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
    local version="$2"
    local component_dir="${TEST_ROOT}/${name}"

    cp -R "${SOURCE_DIR}" "${component_dir}"
    printf '%s\n' "${version}" > "${component_dir}/VERSION"
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
    local version_dir="${release_root}/${version}"

    mkdir -p "${version_dir}"
    printf 'existing release fixture\n' |
        gzip > "${version_dir}/ufm-state-mirror_${version}-docker.img.gz"
}

run_release() {
    local component_dir="$1"
    local version="$2"
    local release_root="$3"

    "${component_dir}/.ci/release_build.sh" "${version}" "${release_root}"
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
ln -s "1.0.1/ufm-state-mirror_1.0.1-docker.img.gz" "${PHYSICAL_ROOT}/latest"
mkdir "${PHYSICAL_ROOT}/.latest.rollback.fixture"
ln -s "1.0.1/ufm-state-mirror_1.0.1-docker.img.gz" \
    "${PHYSICAL_ROOT}/.latest.rollback.fixture/latest"

COMPONENT_8="$(make_component component-8 1.0.1-8)"
run_release "${COMPONENT_8}" "1.0.1-8" "${LOGICAL_ROOT}"
assert_link_target "${PHYSICAL_ROOT}/latest" \
    "${LOGICAL_ROOT}/1.0.1-8/ufm-state-mirror_1.0.1-8-docker.img.gz"
test ! -e "${PHYSICAL_ROOT}/.latest.rollback.fixture"
test "$(stat -c '%a' "${PHYSICAL_ROOT}/1.0.1-8")" = 755
test "$(stat -c '%a' "${PHYSICAL_ROOT}/1.0.1-8/ufm-state-mirror_1.0.1-8-docker.img.gz")" = 644

rm -f "${PHYSICAL_ROOT}/latest"
ln -s "${PHYSICAL_ROOT}/1.0.1-8/ufm-state-mirror_1.0.1-8-docker.img.gz" \
    "${PHYSICAL_ROOT}/latest"
COMPONENT_9="$(make_component component-9 1.0.1-9)"
run_release "${COMPONENT_9}" "1.0.1-9" "${LOGICAL_ROOT}"
assert_link_target "${PHYSICAL_ROOT}/latest" \
    "${LOGICAL_ROOT}/1.0.1-9/ufm-state-mirror_1.0.1-9-docker.img.gz"

rm -f "${PHYSICAL_ROOT}/latest"
ln -s "1.0.1-9/ufm-state-mirror_1.0.1-9-docker.img.gz" "${PHYSICAL_ROOT}/latest"
rm -f "${PHYSICAL_ROOT}/1.0.1-9/ufm-state-mirror_1.0.1-9-docker.img.gz"
COMPONENT_10="$(make_component component-10 1.0.1-10)"
run_release "${COMPONENT_10}" "1.0.1-10" "${LOGICAL_ROOT}"
assert_link_target "${PHYSICAL_ROOT}/latest" \
    "${LOGICAL_ROOT}/1.0.1-10/ufm-state-mirror_1.0.1-10-docker.img.gz"

DOWNGRADE_PHYSICAL_ROOT="${TEST_ROOT}/downgrade-physical"
DOWNGRADE_LOGICAL_ROOT="${TEST_ROOT}/downgrade-logical"
mkdir -p "${DOWNGRADE_PHYSICAL_ROOT}"
ln -s "${DOWNGRADE_PHYSICAL_ROOT}" "${DOWNGRADE_LOGICAL_ROOT}"
ln -s "${DOWNGRADE_PHYSICAL_ROOT}/1.0.2-1/ufm-state-mirror_1.0.2-1-docker.img.gz" \
    "${DOWNGRADE_PHYSICAL_ROOT}/latest"
COMPONENT_99="$(make_component component-99 1.0.1-99)"
if run_release "${COMPONENT_99}" "1.0.1-99" "${DOWNGRADE_LOGICAL_ROOT}"; then
    echo "Expected build-suffix downgrade rejection" >&2
    exit 1
fi

SAME_CORE_ROOT="${TEST_ROOT}/same-core-release"
mkdir -p "${SAME_CORE_ROOT}"
make_artifact "${SAME_CORE_ROOT}" "1.0.1-10"
ln -s "${SAME_CORE_ROOT}/1.0.1-10/ufm-state-mirror_1.0.1-10-docker.img.gz" \
    "${SAME_CORE_ROOT}/latest"
COMPONENT_9_DOWNGRADE="$(make_component component-9-downgrade 1.0.1-9)"
if run_release "${COMPONENT_9_DOWNGRADE}" "1.0.1-9" "${SAME_CORE_ROOT}"; then
    echo "Expected same-core build-suffix downgrade rejection" >&2
    exit 1
fi

UNSAFE_ROLLBACK_ROOT="${TEST_ROOT}/unsafe-rollback-release"
mkdir -p "${UNSAFE_ROLLBACK_ROOT}/.latest.rollback.fixture"
printf 'must be preserved\n' > \
    "${UNSAFE_ROLLBACK_ROOT}/.latest.rollback.fixture/unexpected-data"
COMPONENT_UNSAFE="$(make_component component-unsafe 1.0.1-11)"
if run_release "${COMPONENT_UNSAFE}" "1.0.1-11" "${UNSAFE_ROLLBACK_ROOT}"; then
    echo "Expected unsafe legacy rollback cleanup rejection" >&2
    exit 1
fi
test -f "${UNSAFE_ROLLBACK_ROOT}/.latest.rollback.fixture/unexpected-data"

COMPONENT_INVALID="$(make_component component-invalid 1.0.1-0)"
if run_release "${COMPONENT_INVALID}" "1.0.1-0" "${TEST_ROOT}/invalid-release"; then
    echo "Expected build suffix 0 to be rejected" >&2
    exit 1
fi

echo "StateMirror release helper tests passed"
