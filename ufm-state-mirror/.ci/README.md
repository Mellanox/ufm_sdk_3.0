# ufm-state-mirror CI

This directory owns StateMirror CI definitions used by Blossom jobs.

Release builds must use the StateMirror-owned release matrix files:

- stable: `ufm-state-mirror/.ci/matrix_job_release.yaml`
- nbuprod: `ufm-state-mirror/.ci/matrix_job_release_nbuprod.yaml`

Both matrices delegate the actual release artifact creation to
`ufm-state-mirror/.ci/release_build.sh`.

The nbuprod matrix runs the approved privileged x86_64 DIND builder in the
`il-ipp-blossom-prod` Kubernetes cloud. It starts the nested Docker daemon and
mounts the logical `/auto/mswg` release path plus its
`/auto/sw/release/ufm` physical alias target. Both release matrices pass the
physical StateMirror alias explicitly to the helper, so target recognition does
not depend on how a Kubernetes bind mount reports `pwd -P`.

The release helper groups immutable build artifacts by base version under
`/auto/mswg/release/ufm/ufm-state-mirror/<BASE_VERSION>/`. The `VERSION` file
declares `BASE_VERSION` and a positive numeric `BUILD_NUMBER`; the extended
version is derived as `<BASE_VERSION>-<BUILD_NUMBER>`. The absolute `latest`
symlink is updated only after the artifact is created successfully. A shared
release lock serializes stable, nbuprod, and manual publication. Artifacts and
the `latest`
link are staged and renamed atomically. Published directories use group-writable
setgid mode `2775` with the Blossom release group `sw_ufm` (`GID 4200`), while
artifacts use mode `0644`.
Recognized relative, physical-alias, and legacy flat `latest` targets are
migrated to the canonical grouped path. An interrupted publication is rolled
back or resumed from its build-specific pending marker on the next invocation.
