from fastapi import HTTPException
import bcrypt
from services.db_conn import Database

async def register_user(email: str, password: str):
    db = Database()
    await db.connect()

    try:
        existing = await db.fetchrow(
            "SELECT user_id FROM users WHERE email = $1", email
        )
        if existing:
            raise HTTPException(status_code=409, detail="User already exists.")

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        await db.execute(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2)",
            email, hashed_pw
        )

        return {"message": "User registered successfully."}

    finally:
        await db.close()
