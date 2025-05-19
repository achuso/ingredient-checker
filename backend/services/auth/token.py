import os, jwt, datetime
from fastapi import HTTPException, status
from typing import Dict

SECRET = os.getenv("SECRET_KEY", "totally-safe-secret-not-really-479")
EXPIRY_MIN = int(os.getenv("JWT_MINUTES", "3000"))

def create_access_token(data: Dict) -> str:
    to_encode = {
        **data,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=EXPIRY_MIN),
    }
    return jwt.encode(to_encode, SECRET, algorithm="HS256")

def verify_token(auth_header: str):
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = auth_header.split()[1]
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalid")
