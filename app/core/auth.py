"""Clerk JWT authentication for FastAPI."""

from __future__ import annotations

from typing import Annotated

from clerk_backend_api import AuthenticateRequestOptions, Clerk, Requestish
from clerk_backend_api.security.types import AuthStatus, RequestState
from fastapi import Depends, HTTPException, Query, Request

from app.core.config import get_settings

_clerk_client: Clerk | None = None


def _get_client() -> Clerk:
    global _clerk_client
    if _clerk_client is None:
        secret = get_settings().clerk_secret_key.get_secret_value()
        _clerk_client = Clerk(bearer_auth=secret or None)
    return _clerk_client


def _extract_token(request: Request, token_query: str | None) -> str | None:
    """Token from the Authorization header, else the token query param (SSE)."""
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return token_query or None


def get_current_user(
    request: Request,
    token: str | None = Query(default=None, description="Clerk JWT (SSE fallback)"),
) -> str:
    """Verify the Clerk token and return the user_id (sub claim)."""
    raw_token = _extract_token(request, token)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    settings = get_settings()
    options = AuthenticateRequestOptions(
        secret_key=settings.clerk_secret_key.get_secret_value() or None,
        authorized_parties=settings.clerk_authorized_parties_list,
    )
    state: RequestState = _get_client().authenticate_request(request, options)

    if state.status != AuthStatus.SIGNED_IN or not state.payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = state.payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user identity")
    return user_id


CurrentUser = Annotated[str, Depends(get_current_user)]
