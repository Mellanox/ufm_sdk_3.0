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


def run(classifier: Classifier, store: Store, ufm_version: str) -> int:
    """Restore every entry from the install-wide ``store`` (HLD 5.2.3, 5.3.6)."""
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


def main() -> int:
    import os

    from state_mirror.backends import backend_from_env, build_store
    from state_mirror.logconfig import setup_logging

    global log
    log = setup_logging("state_mirror.restore")
    classifier_path = os.environ.get("CLASSIFIER_PATH", "/etc/state_mirror/state_mirror.yaml")
    ufm_version = os.environ.get("UFM_VERSION", "unknown")
    log.info("state-mirror restore starting (ufm_version=%s)", ufm_version)
    try:
        classifier = Classifier.load_file(classifier_path)
        store = build_store(backend_from_env())
        rc = run(classifier, store, ufm_version)
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
