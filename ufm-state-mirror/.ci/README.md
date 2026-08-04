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
declares both `BASE_VERSION` and `EXTENDED_VERSION`; the latter must equal the
base plus a positive numeric build suffix. The absolute `latest` symlink is
updated only after the artifact is created successfully. A shared release lock
serializes stable, nbuprod, and manual publication. Artifacts and the `latest`
link are staged and renamed atomically. Published directories use mode `0755`
and preserve an inherited setgid bit (`2755`), while artifacts use mode `0644`.
Recognized relative, physical-alias, and legacy flat `latest` targets are
migrated to the canonical grouped path. An interrupted publication is rolled
back or resumed from its build-specific pending marker on the next invocation.
