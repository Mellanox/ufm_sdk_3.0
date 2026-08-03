# ufm-state-mirror CI

This directory owns StateMirror CI definitions used by Blossom jobs.

Release builds must use the StateMirror-owned release matrix files:

- stable: `ufm-state-mirror/.ci/matrix_job_release.yaml`
- nbuprod: `ufm-state-mirror/.ci/matrix_job_release_nbuprod.yaml`

Both matrices delegate the actual release artifact creation to
`ufm-state-mirror/.ci/release_build.sh`.

The nbuprod matrix runs in the approved x86_64 Docker builder container on the
`SWX-CI-DOCKER` agent and mounts the host Docker socket and release share.

The release helper stores one immutable artifact per version under
`/auto/mswg/release/ufm/ufm-state-mirror/<VERSION>/` and updates the absolute
`latest` symlink only after the artifact is created successfully. A shared
release lock serializes stable, nbuprod, and manual publication. Artifacts and
the `latest` link are staged and renamed atomically. Release versions use
numeric `MAJOR.MINOR.PATCH` format. Published directories use mode `0755` and
preserve an inherited setgid bit (`2755`), while artifacts use mode `0644`. An
interrupted publication is rolled back or resumed from its pending marker on
the next invocation.
