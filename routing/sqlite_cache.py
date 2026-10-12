"""Serialize SQLite cache SQL in the local single-process threaded application.

SQLite shared-memory connections can raise SQLITE_LOCKED immediately, ignoring
the busy timeout, when one thread writes while another reads the cache table.
Keep only cache SQL inside this lock; routing and optimization remain concurrent.
Production PostgreSQL uses Django's DatabaseCache directly. This does not claim
coordination between different processes or protect concurrent offline imports.
"""

import threading

from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache.backends.db import DatabaseCache

CACHE_SQL_LOCK = threading.RLock()


class SQLiteDatabaseCache(DatabaseCache):
    def get_many(self, keys, version=None):
        with CACHE_SQL_LOCK:
            return super().get_many(keys, version)

    def _base_set(self, mode, key, value, timeout=DEFAULT_TIMEOUT):
        with CACHE_SQL_LOCK:
            return super()._base_set(mode, key, value, timeout)

    def _base_delete_many(self, keys):
        with CACHE_SQL_LOCK:
            return super()._base_delete_many(keys)

    def has_key(self, key, version=None):
        with CACHE_SQL_LOCK:
            return super().has_key(key, version)

    def clear(self):
        with CACHE_SQL_LOCK:
            return super().clear()
