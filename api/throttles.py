"""Bound public requests in the shared cache without introducing Redis.

The production service runs one threaded worker. Serializing throttle updates
prevents concurrent in-process read/modify/write bypass. A multi-worker service
would need an atomic shared rate limiter before scaling.
"""

import threading

from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle

THROTTLE_LOCK = threading.Lock()


class RouteClientThrottle(SimpleRateThrottle):
    scope = "route_client"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}

    def allow_request(self, request, view):
        if not settings.PUBLIC_API_THROTTLING:
            return True
        with THROTTLE_LOCK:
            return super().allow_request(request, view)


class RouteGlobalThrottle(RouteClientThrottle):
    scope = "route_global"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": "all"}
