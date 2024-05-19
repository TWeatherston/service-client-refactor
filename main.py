from typing import Optional
import os
import logging

from pydantic import BaseModel
from authlib.integrations.httpx_client import AsyncOAuth2Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Auth0Settings(BaseModel):
    domain: str
    client_id: str
    client_secret: str
    audience: str
    auth_base_url: str


class CustomAsyncOAuth2Client(AsyncOAuth2Client):

    def __init__(
        self,
        authorization_base_url: str,
        audience: str,
        cache=None,
        token_cache_buffer: int = 300,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.cache = cache
        self.authorization_base_url = authorization_base_url
        self.audience = audience
        self.token_cache_buffer = token_cache_buffer

    async def fetch_token(self, *args, **kwargs):
        # Get from memory
        if self.token and not self.token.is_expired():
            logger.info("Using m2m token from memory")
            return self.token

        # Get from cache
        logger.info("No m2m token found in memory. Fetching token from cache")
        key = f"{self.client_id}{self.audience}"
        token = self.cache.get(key)
        if token and not token.is_expired():
            logger.info("Retrieved token from the cache")
            self.token = token
            return token

        # Get from token endpoint
        logger.info("No m2m token found in cache. Fetching token from token endpoint")
        token = await super().fetch_token(
            self.authorization_base_url,
            audience=self.audience,
            grant_type="client_credentials",
            **kwargs,
        )
        # Save the token to the cache
        logger.info("Saving m2m token to cache")

        ttl = token.get("expires_in") - self.token_cache_buffer
        if ttl < 0:
            ttl = token.get("expires_in")
        self.cache.set(key, token, ttl)

        return token


class BaseServiceClient:

    def __init__(
        self,
        auth0_settings: Optional[Auth0Settings] = None,
        client: Optional[AsyncOAuth2Client] = None,
    ):
        self._auth0_settings = auth0_settings
        self._client = client

    @property
    def auth0_settings(self):
        """Return the Auth0 settings. If it does not exist, create it by fetching values from the environment."""
        if self._auth0_settings is None:
            self.auth0_settings = Auth0Settings(
                domain=os.getenv("AUTH0_DOMAIN"),
                client_id=os.getenv("AUTH0_CLIENT_ID"),
                client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
                audience=os.getenv("AUTH0_AUDIENCE"),
            )
        return self._auth0_settings

    @property
    def client(self):
        """Return the 0Auth2 client. If it does not exist, create it and fetch the token."""
        if self._client is None:
            self._client = AsyncOAuth2Client(
                client_id=self.auth0_settings.client_id,
                client_secret=self.auth0_settings.client_secret,
            )
            self._client.fetch_token(
                url=self.auth0_settings.auth_base_url,
                grant_type="client_credentials",
                audience=self.auth0_settings.audience,
            )
        return self._client

    async def __aenter__(self):
        return self.client

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        """Close the httpx client to terminate any open connections."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
