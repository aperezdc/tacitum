#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 Igalia S.L.
#
# Distributed under terms of the AGPLv3 license.

from indicium.key import split, join
from indicium.git import GitStore
from indicium.base import Shim
from indicium.cache import LRUCache
import models


class ModelMappingStorage(Shim):
    __slots__ = ("_map",)

    def __init__(self, child, *arg):
        super(ModelMappingStorage, self).__init__(child)
        self._map = {}
        for prefix, cls, attr in arg:
            self._map[prefix] = (cls, attr)

    def put(self, key, value):
        key = split(key)
        if key[0] in self._map:
            cls, attr = self._map[key[0]]
            if not isinstance(value, cls):
                raise RuntimeError("{!r} not mapped to class {!r}".format(key[0], cls))
            suffix = getattr(value, attr, None)
            if suffix is None:
                raise RuntimeError("{!r} does not have a {!r} attribute".format(value, attr))
            key.append(suffix)
        self.child.put(join(key), value.to_hipack(indent=True))

    def get(self, key):
        prefix = split(key)[0]
        if prefix in self._map:
            value = self.child.get(key)
            if value:
                return self._map[prefix][0].from_hipack(value)
            else:
                return None
        raise RuntimeError("No mapping defined for prefix /" + prefix)

    def query(self, pattern, limit=None, offset=0):
        for key, value in self.child.query(pattern, limit, offset):
            prefix = split(key)[0]
            if prefix not in self._map:
                raise RuntimeError("No mapping defined for prefix /" + prefix)
            yield (key, self._map[prefix][0].from_hipack(value))


class TacitumStore(LRUCache):
    __slots__ = ("_gitstore",)

    def __init__(self, path, cache_size=100):
        self._gitstore = GitStore(path, extension=".hipack", autocommit=False)
        super(TacitumStore, self).__init__(ModelMappingStorage(self._gitstore,
                ("user", models.User, "username"),
            ), size=cache_size)

    def commit(self, *arg, **kw):
        self._gitstore.commit(*arg, **kw)
