import hashlib
import json
import threading
from contextlib import contextmanager

from django.core.cache import cache

# Bounded lock stripes coalesce identical requests in this process without
# accumulating endpoint locks. Database cache shares results across processes;
# cross-process cold misses may still each call the provider (documented).
LOCKS = [threading.RLock() for _ in range(64)]
METRIC_LOCK = threading.Lock()


def cache_key(namespace, value):
    return (
        namespace
        + ":"
        + hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()
    )


@contextmanager
def request_lock(key):
    with LOCKS[int(hashlib.sha256(key.encode()).hexdigest(), 16) % len(LOCKS)]:
        yield


def increment_metric(name):
    key = "metric:" + name
    # DatabaseCache.incr is read/modify/write, so serialize process-local metrics.
    with METRIC_LOCK:
        cache.add(key, 0, timeout=None)
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=None)
