from src.Security.security import create_access_token

def test_create_access_token():
    token = create_access_token({"sub": "test"})
    print(token)


test_create_access_token()