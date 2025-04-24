from fastapi import HTTPException, status
import bcrypt
import asyncpg

from services.db_conn import get_db
from services.auth.token import create_access_token

async def login_user(email: str, password: str):
    db = await get_db()

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

    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    finally:
        await db.close()