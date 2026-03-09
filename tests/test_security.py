from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify_roundtrip() -> None:
    password = "StrongPass123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_password_verify_fails_for_wrong_password() -> None:
    hashed = get_password_hash("CorrectPass123")

    assert verify_password("WrongPass123", hashed) is False


def test_access_token_create_and_decode() -> None:
    token = create_access_token("42")
    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert "exp" in payload
