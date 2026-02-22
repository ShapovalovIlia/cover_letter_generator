import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db
from src.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

_COOKIE_NAME = "session"
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE_DAYS = 30


def _create_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(UTC) + timedelta(days=_JWT_EXPIRE_DAYS),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=_JWT_ALGORITHM,
    )


def _decode_jwt(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[_JWT_ALGORITHM],
    )


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=_JWT_EXPIRE_DAYS * 86400,
        path="/",
    )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get(_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = _decode_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(  # noqa: B904
            status_code=401, detail="Session expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(  # noqa: B904
            status_code=401, detail="Invalid session"
        )

    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/login")
async def login(request: Request) -> Response:
    callback_url = str(request.url_for("auth_callback"))
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    from urllib.parse import urlencode

    url = f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"
    return Response(status_code=307, headers={"Location": url})


@router.get("/callback", name="auth_callback")
async def callback(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    callback_url = str(request.url_for("auth_callback"))

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret.get_secret_value(),
                "redirect_uri": callback_url,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()

        userinfo_resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        userinfo_resp.raise_for_status()
        userinfo = userinfo_resp.json()

    google_id = userinfo["sub"]
    stmt = select(User).where(User.google_id == google_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        user.name = userinfo.get("name", user.name)
        user.picture = userinfo.get("picture", user.picture)
        user.email = userinfo.get("email", user.email)
    else:
        user = User(
            google_id=google_id,
            email=userinfo.get("email", ""),
            name=userinfo.get("name", ""),
            picture=userinfo.get("picture", ""),
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    logger.info("User logged in: %s (%s)", user.email, user.id)

    token = _create_jwt(user.id)
    response = Response(
        status_code=307,
        headers={"Location": settings.frontend_url},
    )
    _set_session_cookie(response, token)
    return response


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }


@router.post("/logout")
async def logout() -> Response:
    response = Response(status_code=200)
    response.delete_cookie(_COOKIE_NAME, path="/")
    return response
