import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from services.db_conn import Database, get_db
from services.models import User as UserModel
from services.auth.token import verify_token  # ← use verify_token instead of decode_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_conn: Database = Depends(get_db),
) -> UserModel:
    """
    1) Receive the raw token (no "Bearer " prefix) from OAuth2PasswordBearer
    2) Prepend "Bearer " and call verify_token(...)
    3) Extract 'sub' (user_id) from the payload
    4) Fetch the user from the database
    5) Return a UserModel instance or raise 401 if anything fails
    """

    # 2) Prepend "Bearer " so that verify_token sees "Bearer <token>"
    auth_header = f"Bearer {token}"
    try:
        payload = verify_token(auth_header)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    # 3) Pull the user_id ("sub" claim) from the payload
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user identifier.",
        )

    # 4) Fetch the user from the database
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

    # 5) Construct a UserModel instance (using your ORM/Pydantic class)
    user = UserModel(
        user_id=row["user_id"],
        email=row["email"],
        password_hash=row["password_hash"],
        created_at=row["created_at"],
    )
    return user
