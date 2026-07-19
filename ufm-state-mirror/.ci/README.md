# ufm-state-mirror CI

This directory owns the StateMirror release helper used by the shared
`UFM_PLUGINS_SDK_RELEASE` Blossom job.

The root release matrix dispatches here when the selected release target is
`ufm-state-mirror`. Existing UFM plugins continue to use their own
`plugins/<name>/.ci` and `plugins/<name>/build` layout.
