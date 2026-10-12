from django.urls import path

from api.views import health, optimize_route, stats
from demo.views import index

urlpatterns = [
    path("", index),
    path("api/v1/health/", health),
    path("api/v1/stats/", stats),
    path("api/v1/routes/optimize/", optimize_route),
]
