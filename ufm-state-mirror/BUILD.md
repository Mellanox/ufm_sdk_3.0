# ufm-state-mirror - Build and Release

This process is manual.

The `ufm-state-mirror` image is a **standalone, consumer-agnostic** component.
It ships only the StateMirror engine; the file set it mirrors (the classifier)
is supplied at runtime by each consumer (UFM, UFM HA) via a ConfigMap mounted at
`CLASSIFIER_PATH`. Nothing in this repo is UFM-version-specific.

## Release rules

- `ufm-state-mirror/VERSION` is the release version source of truth and must be committed.
- The image tag is derived from `VERSION` (`mellanox/ufm-state-mirror:<VERSION>`).
- CI already validates lint (`ruff`) and unit tests (`pytest`). The manual steps
  below are for image build verification and publishing.
- Always build from git-tracked files, not from the live working directory.
- Create the tag from the exact same commit that produced the released image.

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

## Phase B - Release from the merged commit

### 1. Check out the merged commit on `main`

```bash
git checkout main
git pull origin main
```

### 2. Build and push the release image from the merged commit

```bash
CHART=ufm-state-mirror
VERSION="$(git show HEAD:${CHART}/VERSION | tr -d '\n')"
STAGE_DIR="$(mktemp -d /tmp/ufm-state-mirror-stage.XXXXXX)"

git archive --format=tar HEAD "${CHART}" | tar -xf - -C "${STAGE_DIR}"

# Authenticate to the registry first (docker login harbor.mellanox.com ...).
REGISTRY=<registry/namespace> PUSH=y \
  "${STAGE_DIR}/${CHART}/build/docker_build.sh" "${VERSION}"
```

### 3. Tag the same commit

```bash
git tag -a "ufm-state-mirror-v${VERSION}" -m "Release ufm-state-mirror ${VERSION}"
git push origin "ufm-state-mirror-v${VERSION}"
```

## Consuming the image

A consumer (the UFM `ufm-enterprise` chart, the UFM HA chart) references the
published image by pinned tag and provides its own classifier:

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
