import os

HTTPS_URLS = bool(os.environ.get("HTTPS_URLS"))
MONGO_HOST = os.environ.get("MONGO_HOST")
MONGO_TLS = bool(os.environ.get("MONGO_TLS"))
MONGO_USER = os.environ.get("MONGO_USER")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD")
ORCID_CLIENT_ID = os.environ.get("ORCID_CLIENT_ID")
ORCID_CLIENT_SECRET = os.environ.get("ORCID_CLIENT_SECRET")
ORCID_REDIRECT_URI = os.environ.get("ORCID_REDIRECT_URI")
API_URI_AUTHORITY = os.environ.get("API_URI_AUTHORITY", "127.0.0.1:8000")
API_URI_SCHEME = os.environ.get("API_URI_SCHEME", "http")

API_BASE_URI = f"{API_URI_SCHEME}://{API_URI_AUTHORITY}"
