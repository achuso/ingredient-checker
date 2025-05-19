import bcrypt
from fastapi import HTTPException
from services.db_conn import Database
from services.auth.token import create_access_token

async def login_user(email: str, password: str):
    db = Database()
    await db.connect()

    try:
        row = await db.fetchrow(
            "SELECT user_id, password_hash FROM users WHERE email = $1", email
        )
        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        user_id = str(row["user_id"])
        peppered = (password + user_id).encode()
        if not bcrypt.checkpw(peppered, row["password_hash"].encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        return {"access_token": create_access_token({"user_id": user_id})}
    finally:
        await db.close()
