import uuid, bcrypt
from fastapi import HTTPException
from services.db_conn import Database

async def register_user(email: str, password: str):
    db = Database()
    await db.connect()

    try:
        # Check if email's taken
        if await db.fetchrow("SELECT 1 FROM users WHERE email=$1", email):
            raise HTTPException(status_code=409, detail="User already exists.")

        user_id = uuid.uuid4()

        # Bcrypt
        peppered = (password + str(user_id)).encode()
        hashed   = bcrypt.hashpw(peppered, bcrypt.gensalt()).decode()

        await db.execute(
            "INSERT INTO users (user_id, email, password_hash) VALUES ($1,$2,$3)",
            user_id, email, hashed
        )
        return {"user_id": str(user_id)}
    finally:
        await db.close()
