from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from shared.jwt_utils import create_access_token

AUTH_SHARED_SECRET = os.getenv("AUTH_SHARED_SECRET", "local-dev-shared-secret")
AUTH_ISSUER = os.getenv("AUTH_ISSUER", "api-testing-auth")
AUTH_AUDIENCE = os.getenv("AUTH_AUDIENCE", "api-testing-api")

app = FastAPI(title="API Testing Auth Service", version="1.0.0")


class TokenRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str


USERS = {
    "tester": {
        "password": "tester-password",
        "role": "tester",
        "scopes": ["orders:write"],
    },
    "admin": {
        "password": "admin-password",
        "role": "admin",
        "scopes": ["orders:write", "admin:reset"],
    },
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "auth-service"}


@app.post("/oauth/token", response_model=TokenResponse)
def issue_token(payload: TokenRequest) -> TokenResponse:
    user = USERS.get(payload.username)
    if user is None or user["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    expires_in = 3600
    access_token = create_access_token(
        subject=payload.username,
        role=user["role"],
        scopes=user["scopes"],
        secret=AUTH_SHARED_SECRET,
        issuer=AUTH_ISSUER,
        audience=AUTH_AUDIENCE,
        lifetime_seconds=expires_in,
    )
    return TokenResponse(access_token=access_token, expires_in=expires_in, scope=" ".join(user["scopes"]))
