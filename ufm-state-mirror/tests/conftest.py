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

"""Shared fixtures for the state_mirror unit tests."""

import fnmatch

import pytest


class _Pipe:
    def __init__(self, store):
        self._store = store
        self._ops = []

    def set(self, key, value):
        self._ops.append(("set", key, value))

    def delete(self, key):
        self._ops.append(("del", key))

    def execute(self):
        for op in self._ops:
            if op[0] == "set":
                self._store[op[1]] = op[2]
            else:
                self._store.pop(op[1], None)


class FakeRedis:
    """Minimal in-memory stand-in for the subset of redis-py the sidecar uses."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)

    def pipeline(self, transaction=True):
        return _Pipe(self.store)

    def keys(self, pattern):
        return [k for k in self.store if fnmatch.fnmatch(k, pattern)]


@pytest.fixture
def fake_redis():
    return FakeRedis()
