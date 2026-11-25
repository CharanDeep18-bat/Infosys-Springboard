
import httpx

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """
    Validate the Supabase access token and return the authenticated user.
    """

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase authentication is not configured",
        )

    token = credentials.credentials

    auth_url = (
        f"{settings.supabase_url.rstrip('/')}/auth/v1/user"
    )

    headers = {
        "apikey": settings.supabase_key,
        "Authorization": f"Bearer {token}",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                auth_url,
                headers=headers,
            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Authentication service is unavailable",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = response.json()

    if not user.get("id"):
        raise HTTPException(
            status_code=401,
            detail="Invalid authenticated user",
        )

    return user
