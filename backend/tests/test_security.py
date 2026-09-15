from app.core.security import get_password_hash, verify_password, create_access_token, verify_token

def test_password_hashing():
    raw = "SuperSecretPassword123"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token():
    user_id = "8f9b117a-1885-4986-ba54-47f1cb47a82d"
    token = create_access_token(subject=user_id, role="ADMIN")
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["role"] == "ADMIN"
