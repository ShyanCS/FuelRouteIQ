import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only-not-for-deployment")
if not DEBUG and (len(SECRET_KEY) < 50 or SECRET_KEY.startswith("local-development")):
    raise ImproperlyConfigured(
        "Production requires a private DJANGO_SECRET_KEY of at least 50 characters"
    )
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if h.strip()
]
if os.getenv("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "stations",
    "demo",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
ROOT_URLCONF = "fuelroute.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]
WSGI_APPLICATION = "fuelroute.wsgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("DATABASE_PATH", str(BASE_DIR / "db.sqlite3")),
        "OPTIONS": {"timeout": 20},
    }
}
if os.getenv("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.parse(
        os.environ["DATABASE_URL"], conn_max_age=60, conn_health_checks=True
    )
    if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
        raise ImproperlyConfigured(
            "DATABASE_URL must be PostgreSQL; use DATABASE_PATH for local SQLite"
        )
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
    db_options = DATABASES["default"].setdefault("OPTIONS", {})
    db_options["connect_timeout"] = 10
    if not DEBUG:
        db_options.setdefault("sslmode", "require")
        if db_options["sslmode"] not in {"require", "verify-ca", "verify-full"}:
            raise ImproperlyConfigured("Production PostgreSQL requires SSL")
if not DEBUG and not os.getenv("DATABASE_URL"):
    raise ImproperlyConfigured("Production requires a durable PostgreSQL DATABASE_URL")
# Shared persistent cache for the local multi-threaded demo; createcachetable installs it.
CACHES = {
    "default": {
        "BACKEND": "routing.sqlite_cache.SQLiteDatabaseCache"
        if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
        else "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "fuelroute_cache",
        "TIMEOUT": 86400,
        "OPTIONS": {"MAX_ENTRIES": 5000},
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "EXCEPTION_HANDLER": "api.errors.exception_handler",
    "NUM_PROXIES": 1 if not DEBUG else 0,
    "DEFAULT_THROTTLE_RATES": {
        "route_client": "30/minute",
        "route_global_minute": "30/minute",
        "route_global": "500/day",
    },
}
PUBLIC_API_THROTTLING = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if not DEBUG else None
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = [
    f"https://{h}" for h in ALLOWED_HOSTS if h not in {"localhost", "127.0.0.1", "testserver"}
]
SECURE_REFERRER_POLICY = "same-origin"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {"django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False}},
}
DATA_UPLOAD_MAX_MEMORY_SIZE = 16_384
ROUTING_PROVIDER = os.getenv("ROUTING_PROVIDER", "ors")
ORS_API_KEY = os.getenv("ORS_API_KEY", "")
ORS_API_BASE_URL = os.getenv("ORS_API_BASE_URL", "https://api.heigit.org/openrouteservice").rstrip(
    "/"
)
ORS_GEOCODING_BASE_URL = os.getenv(
    "ORS_GEOCODING_BASE_URL", "https://api.heigit.org/pelias/v1"
).rstrip("/")
ROUTE_CACHE_TTL_SECONDS = int(os.getenv("ROUTE_CACHE_TTL_SECONDS", "86400"))
GEOCODE_CACHE_TTL_SECONDS = int(os.getenv("GEOCODE_CACHE_TTL_SECONDS", "2592000"))
OPTIMIZATION_CACHE_TTL_SECONDS = int(os.getenv("OPTIMIZATION_CACHE_TTL_SECONDS", "3600"))
CORRIDOR_MILES = float(os.getenv("CORRIDOR_MILES", "5"))
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
