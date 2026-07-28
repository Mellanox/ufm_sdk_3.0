# ufm-state-mirror - Build and Release

The release path is automated through the existing Blossom
`UFM_PLUGINS_SDK_RELEASE` job.

The `ufm-state-mirror` image is a **standalone, consumer-agnostic** component.
It ships only the StateMirror engine; the file set it mirrors (the classifier)
is supplied at runtime by each consumer (UFM, UFM HA) via a ConfigMap mounted at
`CLASSIFIER_PATH`. Nothing in this repo is UFM-version-specific.

## Release rules

- `ufm-state-mirror/VERSION` is the release version source of truth and must be committed.
- The image tag is derived from `VERSION` (`mellanox/ufm-state-mirror:<VERSION>`).
- CI validates lint (`ruff`), unit tests (`pytest`), and a no-push image build.
- Blossom publishes the release artifact as
  `/auto/mswg/release/ufm/ufm-state-mirror/ufm-state-mirror_<VERSION>-docker.img.gz`.
- The StateMirror-specific release matrices and release helper live under
  `ufm-state-mirror/.ci`.
- Always build from git-tracked files, not from the live working directory.
- Create the tag from the exact same commit that produced the released image.
- `ufm-state-mirror` stays at the repository top level. It is released through
  the plugin release job for consistency, but it is not a UFM plugin.

## Phase A - Pre-merge verification

Use this phase to prove the image builds and the tests pass before the PR is merged.

### 1. Lint and unit test

```bash
cd ufm-state-mirror
pip install -r requirements.txt ruff pytest
ruff check .
ruff format --check .
pytest -q
```

### 2. Build a verification image from the committed snapshot

```bash
CHART=ufm-state-mirror
VERSION="$(git show HEAD:${CHART}/VERSION | tr -d '\n')"
STAGE_DIR="$(mktemp -d /tmp/ufm-state-mirror-stage.XXXXXX)"

git archive --format=tar HEAD "${CHART}" | tar -xf - -C "${STAGE_DIR}"

REGISTRY=mellanox "${STAGE_DIR}/${CHART}/build/docker_build.sh" "${VERSION}"
```

This image is for verification only. Do not push it and do not tag this commit yet.

### 3. Open and merge the PR

Merge only after:

- the verification image build above succeeds
- the `ufm-state-mirror` CI job passes
- the PR is approved and merged

## Phase B - Automated release from the merged commit

### 1. Check out the merged commit on `main`

```bash
git checkout main
git pull origin main
```

### 2. Run the Blossom release job

Run `UFM_PLUGINS_SDK_RELEASE` from the merged commit.

Use these parameters:

- `sha1`: the merged commit SHA, release branch, or `main` after it contains the
  version bump.
- `PLUGIN_VERSION`: the exact content of `ufm-state-mirror/VERSION`.
- Stable job selector: `Plugin_name=ufm-state-mirror`.
- Nbuprod job selector: `PLUGIN_NAME=ufm-state-mirror`.
- Stable `conf_file`: `ufm-state-mirror/.ci/matrix_job_release.yaml`.
- Nbuprod `conf_file`: `ufm-state-mirror/.ci/matrix_job_release_nbuprod.yaml`.

The matrix job fails fast if `PLUGIN_VERSION` does not match
`ufm-state-mirror/VERSION` or if the target artifact already exists.
The StateMirror release matrices dispatch to
`ufm-state-mirror/.ci/release_build.sh`.

Expected output:

```text
/auto/mswg/release/ufm/ufm-state-mirror/ufm-state-mirror_<VERSION>-docker.img.gz
```

### 3. Tag the same commit

After the Blossom job succeeds, tag the commit that produced the artifact:

```bash
VERSION="$(git show HEAD:ufm-state-mirror/VERSION | tr -d '\n')"
git tag -a "ufm-state-mirror-v${VERSION}" -m "Release ufm-state-mirror ${VERSION}"
git push origin "ufm-state-mirror-v${VERSION}"
```

## Manual fallback

Use this only if the Blossom job is unavailable. It should produce the same
`.img.gz` artifact from a committed snapshot:

```bash
CHART=ufm-state-mirror
VERSION="$(git show HEAD:${CHART}/VERSION | tr -d '\n')"
STAGE_DIR="$(mktemp -d /tmp/ufm-state-mirror-stage.XXXXXX)"
OUT_DIR="/auto/mswg/release/ufm/${CHART}"

git archive --format=tar HEAD "${CHART}" | tar -xf - -C "${STAGE_DIR}"

REGISTRY=mellanox "${STAGE_DIR}/${CHART}/build/docker_build.sh" "${VERSION}" "${OUT_DIR}"
```

## Consuming the image

A consumer (the UFM `ufm-enterprise` chart, the UFM HA chart) loads or publishes
the released artifact under the pinned image tag and provides its own classifier:

- `image: <registry>/ufm-state-mirror:<VERSION>` on the init container
  (`python -m state_mirror.restore`) and the native sidecar
  (`python -m state_mirror.mirror`, the image default).
- A ConfigMap with the consumer's classifier mounted at the path given by
  `CLASSIFIER_PATH` (default `/etc/state_mirror/state_mirror.yaml`).

See `examples/classifier-example.yaml` for the classifier schema. The
authoritative, file-set-reconciled classifier lives in the consumer repo, not
here.

## Why this flow

- The pre-merge build proves the image really builds before approval.
- The post-merge build guarantees the published image comes from the merged commit.
- `git archive` keeps untracked files, caches, and other local leftovers out of
  the image.
