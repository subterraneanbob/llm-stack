import pytest
from datetime import datetime

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)


def test_hash_password():
    plain_text_password = "my_secret_P@ssw0rd"
    hashed_password = hash_password(plain_text_password)

    assert hashed_password != plain_text_password
    assert verify_password(plain_text_password, hashed_password) is True
    assert verify_password("incorrect_password", hashed_password) is False


def test_generate_token():
    subject = "42"
    role = "user"
    token = create_access_token(subject, role)

    payload = decode_token(token)

    match payload:
        case {
            "sub": actual_subject,
            "role": actual_role,
            "type": "access",
            "iat": issued_at,
            "exp": expires_at,
        }:
            assert actual_subject == subject
            assert actual_role == role
            assert datetime.fromtimestamp(issued_at) < datetime.fromtimestamp(
                expires_at
            )
        case _:
            pytest.fail("Invalid access token payload")
