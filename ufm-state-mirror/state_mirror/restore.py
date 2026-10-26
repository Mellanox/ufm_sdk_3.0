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

"""StateMirror init container: materialize the storage backend -> emptyDir
before UFM starts (HLD 5.3.2 / 5.3.6 / 5.3.8).

Runs once, to completion, as a Kubernetes init container so UFM never starts on
partial state. Every classifier entry is either restored from the backend or,
on first install (no stored object), seeded from its baseline. Any restore
failure exits non-zero so the pod fails closed rather than booting UFM on
incomplete state.
"""

from __future__ import annotations

import logging
import sys

from state_mirror.classifier import Classifier
from state_mirror.handlers import make_handler
from state_mirror.store import Store

log = logging.getLogger("state_mirror.restore")


def run(classifier: Classifier, store: Store, ufm_version: str, *, handoff_dir=None) -> int:
    """Restore every entry from the install-wide ``store`` (HLD 5.2.3, 5.3.6)."""
    try:
        store = restore_store(classifier, store, ufm_version, handoff_dir)
    except Exception:
        log.exception("restore transaction validation failed")
        return 1
    log.info("restore: %d classifier entries", len(classifier))
    restored, bootstrapped = 0, 0
    written_by = _written_by()
    for entry in classifier.entries:
        handler = make_handler(entry, store, ufm_version, written_by)
        try:
            if handler.restore():
                restored += 1
                log.info("restored %s", entry.path)
            else:
                handler.bootstrap()
                bootstrapped += 1
                log.info("bootstrapped %s (baseline=%s)", entry.path, entry.baseline.value)
        except Exception:
            log.exception("restore failed for entry %s; failing closed", entry.path)
            return 1
    log.info("restore complete: %d restored, %d bootstrapped", restored, bootstrapped)
    return 0


def restore_store(classifier, store, version, handoff_dir=None):
    from state_mirror.generation import GenerationStore, require_checkpoint
    from state_mirror.upgrade import (
        UpgradeError,
        release_authority,
        validate_preservation,
    )
    from state_mirror.upgrade_handoff import _read_handoff_dir

    manifest, source_version = release_authority(store, classifier)
    digest = classifier.digest()
    if manifest and manifest.classifier_digest and manifest.classifier_digest != digest:
        raise UpgradeError("restore classifier digest conflicts with durable release")
    if handoff_dir is not None:
        values, data = _read_handoff_dir(handoff_dir)
        if values["STATE_MIRROR_CLASSIFIER_DIGEST"] != digest:
            raise UpgradeError("restore handoff classifier digest conflicts")
        if values["STATE_MIRROR_TARGET_VERSION"] != version:
            raise UpgradeError("restore target release conflicts")
        operation = values["STATE_MIRROR_OPERATION_ID"]
        committed = manifest and manifest.operation_id == operation
        mode = values["STATE_MIRROR_UPGRADE_MODE"]
        if committed and mode != "committed":
            raise UpgradeError(
                "durable operation is committed; refresh the stale mounted handoff before restore"
            )
        if committed and manifest.target_version != version:
            raise UpgradeError("restore committed release conflicts")
        if mode == "upgrade" and not committed:
            validate_preservation(classifier, data)
            if source_version != values["STATE_MIRROR_SOURCE_VERSION"]:
                raise UpgradeError("restore source release conflicts")
            require_checkpoint(
                store, manifest.generation if manifest else "", digest, operation, version
            )
        elif mode == "committed" and not committed:
            raise UpgradeError("restore committed handoff has no matching durable manifest")
        elif mode == "fresh" and source_version is not None and not committed:
            raise UpgradeError("fresh restore conflicts with durable release")
    elif source_version is not None and source_version != version:
        raise UpgradeError("restore release change requires a checkpoint-bound handoff")
    import json

    from state_mirror.generation import fence_key, record, verify_inventory

    generation = manifest.generation if manifest else ""
    fence = record(store, fence_key(generation))
    if fence and json.loads(fence[0]).get("lock"):
        raise UpgradeError("restore blocked by an interrupted writer mutation")
    selected = GenerationStore(store, generation, readonly=True)
    if generation:
        verify_inventory(selected)
    return selected


def main() -> int:
    import os

    from state_mirror.backends import backend_from_env, build_store
    from state_mirror.logconfig import setup_logging

    global log
    log = setup_logging("state_mirror.restore")
    classifier_path = os.environ.get("CLASSIFIER_PATH", "/etc/state_mirror/state_mirror.yaml")
    from state_mirror.upgrade import release_version_from_env

    try:
        ufm_version = release_version_from_env()
    except Exception:
        log.exception("authoritative UFM release version is required")
        return 1
    log.info("state-mirror restore starting (ufm_version=%s)", ufm_version)
    try:
        classifier = Classifier.load_file(classifier_path)
        store = build_store(backend_from_env())
        from state_mirror.upgrade import DEFAULT_HANDOFF_DIR, HANDOFF_DIR_ENV

        handoff_dir = os.environ.get(HANDOFF_DIR_ENV)
        if handoff_dir is None and os.path.exists(os.path.join(DEFAULT_HANDOFF_DIR, "upgrade.env")):
            handoff_dir = DEFAULT_HANDOFF_DIR
        rc = run(classifier, store, ufm_version, handoff_dir=handoff_dir)
    except Exception:
        log.exception("restore failed; refusing to start UFM on incomplete state")
        return 1
    if rc == 0:
        log.info("state-mirror restore finished successfully")
    return rc


def _written_by() -> str:
    import os

    return "state-mirror:" + os.environ.get("STATE_MIRROR_GIT_SHA", "dev")


if __name__ == "__main__":
    sys.exit(main())
