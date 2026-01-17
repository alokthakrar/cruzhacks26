from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from .config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)

# Cache for JWKS
_jwks_cache: Optional[Dict] = None

# Default dev user ID when auth is skipped
DEV_USER_ID = "dev_user_123"


async def get_jwks() -> Dict:
    """Fetch and cache JWKS from Auth0."""
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.auth0_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache


def get_signing_key(jwks: Dict, token: str) -> str:
    """Extract the signing key from JWKS based on token header."""
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find signing key",
    )


async def verify_token(
    credentials: HTTPAuthorizationCredentials,
) -> Dict:
    """Verify Auth0 JWT token and return payload."""
    token = credentials.credentials

    try:
        jwks = await get_jwks()
        signing_key = get_signing_key(jwks, token)

        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[settings.auth0_algorithms],
            audience=settings.auth0_api_audience,
            issuer=settings.auth0_issuer,
        )
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to verify token: {str(e)}",
        )


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Extract user ID from token, or return dev user if auth is skipped."""
    # Skip auth in development mode
    if settings.skip_auth:
        return DEV_USER_ID

    # Auth required but no credentials provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Verify the token
    payload = await verify_token(credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
        )
    return user_id
