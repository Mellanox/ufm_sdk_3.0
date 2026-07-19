# ufm-state-mirror CI

This directory owns StateMirror CI definitions used by Blossom jobs.

Release builds must use the StateMirror-owned release matrix files:

- stable: `ufm-state-mirror/.ci/matrix_job_release.yaml`
- nbuprod: `ufm-state-mirror/.ci/matrix_job_release_nbuprod.yaml`

Both matrices delegate the actual release artifact creation to
`ufm-state-mirror/.ci/release_build.sh`.
