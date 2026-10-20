# StateMirror upgrade and recovery contract

StateMirror owns durable capture, checkpoint acknowledgement, restore and atomic
publication. The consumer owns stopping application writers, running migration,
preserving the classified paths during installation, and keeping application
startup blocked until `commit` succeeds. These contracts apply to both Redis and
ConfigMap installations. No UFM chart or application changes are included here.

## Release and classifier identity

Set `UFM_RELEASE_VERSION` to the installed UFM release in restore and mirror.
Set `STATE_MIRROR_TARGET_VERSION` for commit, or supply `UFM_RELEASE_VERSION`.
When both exist they must match exactly. For compatibility with the existing UFM chart, an explicit `UFM_VERSION` is
accepted as the release input when neither dedicated variable is supplied.
The chart sets it from `Chart.AppVersion`; consumers must not supply a component
or image build version there. A dedicated release input takes precedence over
`UFM_VERSION`. There is no default `unknown` release. Missing, invalid,
conflicting and downgrade releases fail closed.
Preflight receives its target explicitly through `--target-version`.

The schema-2 durable manifest is the release-level source of truth. Per-object
version stamps are historical once this manifest exists. Before adoption, every
present, verified legacy object must have exactly the same valid release stamp.
Timestamps, newest writes and maximum versions cannot resolve disagreement.
Mixed legacy versions require operator investigation; startup and restore reject
them too, so reconciliation cannot erase the evidence before preflight.
Schema-1 manifests remain readable as source authority but are adopted through a
checkpoint and complete generation publication, even for the same release.

`STATE_MIRROR_CLASSIFIER_DIGEST` is a SHA-256 hash of effective classifier
semantics: normalized lexical absolute paths, handlers, backend keys/prefixes,
recursion, baselines, snapshot policy and timing settings. Entry ordering, YAML
formatting, comments and explicitly supplied defaults do not change it. Paths
are not resolved through container-specific symlinks while calculating identity.
Preflight, mounted/live handoffs, the preservation list, checkpoint, restore,
manifest and writer fence must agree. A changed classifier requires resolving
the transaction before proceeding; the current protocol does not automatically
reconcile different source/target classifier definitions.

## Consumer sequence

1. Deploy a checkpoint-capable StateMirror writer before attempting this
   protocol. Every writer must use its fenced store; older images or direct
   backend clients bypass fencing. Run one application writer per dataset.
2. Run `python -m state_mirror.upgrade preflight` with the existing arguments:
   `--classifier`, `--target-version`, `--namespace`, `--handoff-configmap`,
   `--source-gv-configmap`, and `--source-gv-key`. Keep that exact classifier
   through the entire transaction. Preflight is a preparation step, not a final
   durability acknowledgement.
3. Stop/quiesce **all** UFM writers to classified state, including background
   jobs and SQLite transactions. Keep them stopped. Then, inside the source
   pod's StateMirror container, run:

   ```sh
   python -m state_mirror.upgrade checkpoint \
     --handoff-configmap <prepared-handoff-name> --quiesced --timeout 120
   ```

   `--quiesced` is the consumer's explicit attestation; StateMirror cannot stop
   writers in another container. The command calls the local sidecar's
   `/checkpoint` POST endpoint. Only loopback callers can use it. The endpoint
   validates the authoritative live handoff and preservation list, serializes
   against reconciliation, stops/drains the watcher, flushes observed deletes,
   forces fresh SQLite backups and a full scan, and refuses unresolved drift
   or failed work. It then CAS-freezes the source writer fence. Only after this
   durable fence succeeds does it acknowledge the operation ID and digest.
   A timeout or nonzero exit is **not** acknowledgement. Retry the identical
   request; a durable matching fence makes a lost response retryable.
4. Only after acknowledgement may the consumer remove the source pod. Mount the
   prepared handoff into restore at `STATE_MIRROR_UPGRADE_HANDOFF_DIR` (default
   `/var/run/state-mirror-upgrade`). Restore checks the digest, preservation
   list, release identity and acknowledged source checkpoint before touching
   classified files. It reads only the selected source generation. Baselines
   materialize locally without publishing into the frozen source dataset.
5. Preserve the handoff's exact `preserve-paths.txt` set while installing target
   files. Finish migration with application writers still stopped. Supply the
   same `CLASSIFIER_PATH`, handoff directory and target release, then run:

   ```sh
   python -m state_mirror.upgrade commit
   ```

   Commit captures all current classified files into a fresh, isolated
   generation, including SQLite online backups and directory fan-out. It
   records hashes from the captured bytes in a complete inventory, reads back
   all objects, verifies hashes and exact key membership, rechecks the live
   handoff, and CAS-switches the manifest to that generation and release.
   The source generation is never rewritten by commit. Missing optional paths
   are recorded by absence; files deleted during migration do not fall back to
   old source keys. Only then is the handoff marked committed.
6. Start the target application and target StateMirror writer after commit
   succeeds. The writer pins the manifest generation and checks release/digest
   authority. Each write/delete maintains the generation inventory under its
   writer guard. The old generation remains frozen permanently.

A fresh installation still publishes its initial classified dataset before
commit succeeds, but has no source checkpoint to require. A same-release
schema-2 transaction reuses the committed manifest; migration is not replayed.
On a pod restart, the consumer must determine whether the operation is already
committed **before** rerunning migration. Re-run preflight to refresh a stale
handoff; do not interpret a projected ConfigMap still saying `upgrade` as proof
that commit did not happen. When the manifest records a committed operation but the mounted handoff still
says `upgrade` or `fresh`, restore fails before touching classified files. Refresh
the mounted handoff to `committed`, then retry restore: it selects the complete
target generation and the consumer skips migration. This avoids target state
being migrated twice or overwritten by fresh-install defaults.

## Atomicity and fencing

Generations are physical key namespaces `state-mirror:generation:<id>:`. The
manifest `state-mirror:upgrade-manifest` is the only active-generation pointer;
there is no fallback to legacy keys when a generation object is absent.
Inventories include empty datasets and enforce complete membership on restore.

Each generation has a `state-mirror:fence:<id>` control object (`legacy` for the
old unprefixed keyspace). A writer CAS-acquires a unique mutation lock, writes
its object plus inventory, then CAS-releases the lock. Checkpoint may freeze
only an unlocked fence. Redis uses atomic Lua compare-and-set over body+meta;
ConfigMap uses resourceVersion compare-and-set. Neither backend needs an atomic
multi-object data transaction: the guard excludes checkpoint while writes are
in flight, and the pointer excludes incomplete candidate generations.

An uncertain mutation leaves its guard busy. It has no timeout/automatic lock
stealing: a delayed API request must never become a late writer after fencing.
The sidecar stays alive but further mutations and restore fail closed until
operator recovery. This increases backend operations per mutation (especially
ConfigMap inventory updates) and favors correctness over throughput. ConfigMap
size limits apply to inventory/control objects too; oversized publication fails
without switching the pointer. Use Redis for larger/high-churn datasets.

## Interruption recovery

| Interruption | Durable authority | Recovery |
|---|---|---|
| Before checkpoint acknowledgement | Source still active, or freeze response uncertain | Keep source/application writers quiesced; retry identical checkpoint. Do not remove the pod until acknowledged. |
| A delete event was dropped | Backend may retain the deleted object | Full scan must show no unresolved missing objects before checkpoint; reconcile the file/backend explicitly. A historical drop counter alone is not a veto after drift resolves. |
| During candidate data/inventory writes or verification | Source manifest unchanged | Discard the target pod's partial local migration as needed, restore source, rerun migration and commit. Retry creates a new generation; abandoned candidates stay inactive. |
| Manifest CAS rejected | Winning manifest remains authoritative | Re-read authority; never overwrite a different operation/release. Investigate concurrent upgrades. |
| Manifest persisted but response or handoff update lost | Complete target generation selected | Retry the same commit to finish handoff; it does not recapture data or replay migration. Refresh handoff before a restarted consumer decides whether to migrate. |
| Writer data/inventory write or unlock interrupted | Fence remains busy; data may be partially updated | Stop and prove termination of every old writer and outstanding backend request. Back up data, inventory, manifest and fence. Restore a verified backup or reconcile object+inventory under exclusive maintenance, then repair the matching fence using CAS. Never clear a busy guard on a running writer or on elapsed time alone. |
| Digest/release/preservation mismatch | Existing authority unchanged | Restore the exact prepared classifier/release/handoff or investigate a new transaction; do not edit the digest or version merely to bypass validation. |
| Migration fails before pointer switch | Frozen source remains recoverable | Retry from restored source. Returning to the old release requires explicitly reauthorizing its writer after cancelling the handoff and proving no target writer can run; no automatic thaw/downgrade is provided. |

Keep the frozen source generation and backend backups until the target release
has been validated. Candidate/source garbage collection is deliberately manual:
first prove that no active manifest, handoff, writer or recovery process can
reference the generation. Deleting it early removes the rollback/recovery copy.

## Validation coverage

`tests/test_generation.py` and `tests/test_upgrade.py` run the same transaction
and interruption scenarios against RedisStore and ConfigMapStore adapters with
in-memory protocol fakes. They cover data/inventory write interruptions,
readback corruption, before/after-manifest response loss, handoff CAS conflicts,
checkpoint response loss/restart retry, busy/frozen writers, slow writes crossing
a timestamp boundary, canonical digest mismatch, divergent legacy startup,
SQLite WAL snapshots, directory fan-out and successive upgrades.
`tests/test_health.py` exercises the HTTP checkpoint acknowledgement path.
These tests do not replace deployment-level failover and API outage testing on
an actual Redis/Sentinel or Kubernetes installation.

## UFM integration checked in the companion worktree

The companion UFM chart currently supplies `UFM_VERSION` from `Chart.AppVersion`,
which remains supported. Its commit container mounts migrated files and the
classifier; the classifier defaults to the SDK's default path. A custom classifier
mount also requires `CLASSIFIER_PATH` in the commit container.

The consumer still needs to wire the checkpoint call after actual source-writer
quiescence and before source pod replacement, and mount the handoff into the
restore container (including credentials if live ConfigMap refresh is used).
Its current hook calls preparation/preflight only. The SDK intentionally refuses
a release-changing restore without the checkpoint-bound handoff. On a restart
following a lost manifest response, refresh the handoff before the UFM installer
reads it so `committed` skips migration. Those chart/shutdown changes belong to
the UFM repository and are outside this StateMirror change.
