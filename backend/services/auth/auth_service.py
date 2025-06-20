import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from services.db_conn import Database, get_db
from services.models import User as UserModel
from services.auth.token import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_conn: Database = Depends(get_db),
) -> UserModel:
    auth_header = f"Bearer {token}"
    try:
        payload = verify_token(auth_header)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user identifier.",
        )

    row = await db_conn.fetchrow(
        "SELECT user_id, email, password_hash, created_at "
        "FROM users WHERE user_id = $1",
        user_id,
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    user = UserModel(
        user_id=row["user_id"],
        email=row["email"],
        password_hash=row["password_hash"],
        created_at=row["created_at"],
    )
    return user
