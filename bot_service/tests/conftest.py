import time

import pytest
from jose import jwt

from app.core.config import settings

TOKEN_TTL = 3600


def generate_claims() -> dict:
    subject = "47"
    role = "user"
    issued_at = int(time.time())
    expires_at = issued_at + TOKEN_TTL

    return {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": issued_at,
        "exp": expires_at,
    }


@pytest.fixture
def access_token() -> str:
    return jwt.encode(generate_claims(), settings.jwt_secret, settings.jwt_alg)


@pytest.fixture
def expired_access_token() -> str:
    claims = generate_claims()
    claims["iat"] -= TOKEN_TTL * 2
    claims["exp"] -= TOKEN_TTL * 2

    return jwt.encode(claims, settings.jwt_secret, settings.jwt_alg)
