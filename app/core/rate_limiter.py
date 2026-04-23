# rate_limiter.py configures slowapi rate limiting for HERVEX.
# Rate limiting prevents abuse and protects against runaway
# API usage that would exhaust Groq and Tavily quotas.
#
# slowapi is a FastAPI-compatible rate limiting library
# built on top of limits — it uses Redis as the storage
# backend so limits are shared across multiple workers.

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Initialize limiter using the client's IP address as the key
# get_remote_address extracts the IP from the request
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL  # Shared state across workers
)
