# UFM Plugins Helm Chart - Build and Release

This process is manual.

## Release rules

- `ufm-plugin-helm-template/VERSION` is the release version source of truth and must be committed.
- Do not edit `Chart.yaml` by hand for a release. The release version is injected by `helm package --version --app-version`.
- CI already validates linting and templating. The manual steps below are for release verification and publishing.
- Always build from git-tracked files, not from the live working directory.
- Copy the final artifact only to the internal NFS path.
- Create the tag from the exact same commit that produced the released artifact.

## Phase A - Pre-merge verification

Use this phase to prove the chart packages successfully before the PR is merged.

### 1. Commit the chart changes

Update `ufm-plugin-helm-template/VERSION` with the new semver and commit the chart changes on your branch.

### 2. Sanity-check the chart directory

```bash
git status --short --ignored -- ufm-plugin-helm-template
```

Expected result: no output.

If anything appears here, clean it up first or update `.helmignore` if the file should never be packaged.

### 3. Build a verification package from the committed snapshot

```bash
CHART=ufm-plugin-helm-template
VERSION="$(git show HEAD:${CHART}/VERSION | tr -d '\n')"
STAGE_DIR="$(mktemp -d /tmp/ufm-plugin-helm-stage.XXXXXX)"
OUT_DIR="$(mktemp -d /tmp/ufm-plugin-helm-out.XXXXXX)"

git archive --format=tar HEAD "${CHART}" | tar -xf - -C "${STAGE_DIR}"

helm package "${STAGE_DIR}/${CHART}" \
  --version "${VERSION}" \
  --app-version "${VERSION}" \
  --destination "${OUT_DIR}"

ls -1 "${OUT_DIR}/ufm-plugins-${VERSION}.tgz"
```

This package is for verification only. Do not upload it and do not tag this commit yet.

### 4. Open and merge the PR

Merge only after:

- the verification package command above succeeds
- the Helm CI job passes
- the PR is approved and merged

## Phase B - Release from the merged commit

### 1. Check out the merged commit on `main`

```bash
git checkout main
git pull origin main
git status --short --ignored -- ufm-plugin-helm-template
```

Expected result: no output.

### 2. Build the release artifact from the merged commit

```bash
CHART=ufm-plugin-helm-template
VERSION="$(git show HEAD:${CHART}/VERSION | tr -d '\n')"
STAGE_DIR="$(mktemp -d /tmp/ufm-plugin-helm-stage.XXXXXX)"
OUT_DIR="$(mktemp -d /tmp/ufm-plugin-helm-out.XXXXXX)"

git archive --format=tar HEAD "${CHART}" | tar -xf - -C "${STAGE_DIR}"

helm package "${STAGE_DIR}/${CHART}" \
  --version "${VERSION}" \
  --app-version "${VERSION}" \
  --destination "${OUT_DIR}"
```

### 3. Copy the artifact to the internal location

```bash
cp "${OUT_DIR}/ufm-plugins-${VERSION}.tgz" <internal-nfs-path>
```

Replace `<internal-nfs-path>` with the private internal NFS mount.

### 4. Tag the same commit

```bash
git tag -a "ufm-plugins-helm-v${VERSION}" -m "Release ufm-plugins Helm chart ${VERSION}"
git push origin "ufm-plugins-helm-v${VERSION}"
```

## Why this flow

- The pre-merge build proves the chart really packages before approval.
- The post-merge build guarantees the published artifact comes from the merged commit.
- `git archive` keeps untracked files, ignored files, `.DS_Store`, test output, and other local leftovers out of the package.
