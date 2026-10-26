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

"""Acknowledged final checkpoint, requested only after UFM writer quiescence."""

from __future__ import annotations

import json
import os
import urllib.request

from state_mirror.generation import FencedStore
from state_mirror.upgrade import validate_preservation
from state_mirror.upgrade_contract import SOURCE_UID_ANNOTATION, UpgradeError
from state_mirror.upgrade_handoff import _find_handoff, _validate_handoff_payload


def final_checkpoint(mirror, classifier, api, request):
    """Drain and fence on the same lock as every mirror reconciliation.

    Quiescence is an explicit attestation from the UFM shutdown coordinator;
    StateMirror cannot stop application writers in another container.
    """
    if request.get("quiesced") is not True:
        raise UpgradeError("UFM writer quiescence must be acknowledged")
    operation_id = request.get("operation_id")
    handoff = _find_handoff(api, operation_id)
    values = _validate_handoff_payload(handoff["data"])
    bound_uid = (handoff.get("annotations") or {}).get(SOURCE_UID_ANNOTATION)
    if bound_uid and bound_uid != os.environ.get("STATE_MIRROR_POD_UID"):
        raise UpgradeError("checkpoint source pod UID conflicts")
    digest = classifier.digest()
    if values["STATE_MIRROR_UPGRADE_MODE"] != "upgrade":
        raise UpgradeError("checkpoint requires a prepared upgrade handoff")
    if values["STATE_MIRROR_CLASSIFIER_DIGEST"] != digest or request.get("digest") != digest:
        raise UpgradeError("checkpoint classifier digest conflicts")
    validate_preservation(classifier, handoff["data"])
    target = values["STATE_MIRROR_TARGET_VERSION"]
    if request.get("target_version") != target:
        raise UpgradeError("checkpoint target release conflicts")
    store = mirror.store
    if not isinstance(store, FencedStore):
        raise UpgradeError("checkpoint requires a fenced writer")
    if values["STATE_MIRROR_SOURCE_VERSION"] != store.version:
        raise UpgradeError("checkpoint source release conflicts")

    def validate_live():
        if _find_handoff(api, operation_id) != handoff:
            raise UpgradeError("handoff changed during final checkpoint")

    mirror.final_checkpoint(operation_id, target, validate_live)
    return {"operation_id": operation_id, "digest": digest, "acknowledged": True}


def request_checkpoint(api, handoff_name, *, timeout=120.0):
    handoff = api.read_cm(handoff_name)
    if handoff is None:
        raise UpgradeError("checkpoint handoff ConfigMap is missing")
    values = _validate_handoff_payload(handoff.get("data"))
    payload = {
        "quiesced": True,
        "operation_id": values["STATE_MIRROR_OPERATION_ID"],
        "target_version": values["STATE_MIRROR_TARGET_VERSION"],
        "digest": values["STATE_MIRROR_CLASSIFIER_DIGEST"],
    }
    port = int(os.environ.get("STATE_MIRROR_METRICS_PORT", "9180"))
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/checkpoint",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        ack = json.load(response)
    if ack != {
        "operation_id": payload["operation_id"],
        "digest": payload["digest"],
        "acknowledged": True,
    }:
        raise UpgradeError("checkpoint acknowledgement conflicts")
    return ack
