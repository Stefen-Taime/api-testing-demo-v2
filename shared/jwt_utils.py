from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


class JWTValidationError(Exception):
    """Raised when a JWT is missing, malformed, expired, or signed with the wrong key."""


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def create_access_token(
    *,
    subject: str,
    role: str,
    scopes: list[str],
    secret: str,
    issuer: str,
    audience: str,
    lifetime_seconds: int = 3600,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "scope": " ".join(scopes),
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + lifetime_seconds,
    }
    if additional_claims:
        payload.update(additional_claims)

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(*, token: str, secret: str, issuer: str, audience: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise JWTValidationError("Token must have three parts")

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    provided_signature = _b64url_decode(signature_b64)

    if not hmac.compare_digest(expected_signature, provided_signature):
        raise JWTValidationError("Token signature is invalid")

    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
    except (json.JSONDecodeError, ValueError) as exc:
        raise JWTValidationError("Token payload is malformed") from exc

    if header.get("alg") != "HS256":
        raise JWTValidationError("Unsupported JWT algorithm")

    now = int(time.time())
    if int(payload.get("exp", 0)) < now:
        raise JWTValidationError("Token is expired")
    if payload.get("iss") != issuer:
        raise JWTValidationError("Token issuer is invalid")

    aud = payload.get("aud")
    if isinstance(aud, list):
        valid_audience = audience in aud
    else:
        valid_audience = aud == audience
    if not valid_audience:
        raise JWTValidationError("Token audience is invalid")

    return payload


def scopes_from_claims(claims: dict[str, Any]) -> set[str]:
    scope_value = claims.get("scope", "")
    if isinstance(scope_value, str):
        return {scope for scope in scope_value.split() if scope}
    return set()
