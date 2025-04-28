from services.db_conn import Database
from services.auth.token import create_access_token
from fastapi import HTTPException
import bcrypt

async def login_user(email: str, password: str):
    db = Database()
    await db.connect()

    try:
        row = await db.fetchrow(
            "SELECT user_id, password_hash FROM users WHERE email = $1", email
        )

        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"sub": str(row["user_id"])})
        return {"access_token": token, "token_type": "bearer"}

    finally:
        await db.close()
