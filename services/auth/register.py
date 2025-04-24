from fastapi import HTTPException, status
import asyncpg
import bcrypt

from services.db_conn import get_db

async def register_user(email: str, password: str):
    db = await get_db()

    try:
        # Check if user already exists
        existing = await db.fetchrow("SELECT user_id FROM users WHERE email = $1", email)
        if existing:
            raise HTTPException(status_code=409, detail="User already exists.")

        # Hash password
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Insert user
        await db.execute(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2)",
            email, hashed_pw
        )

        return {"message": "User registered successfully."}

    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="User already exists.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        await db.close()