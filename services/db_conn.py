import asyncpg
import os
from fastapi import HTTPException

async def get_db():
    try:
        return await asyncpg.connect(
            # These are set in AWS Lambda environment variables
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PWD"),
            database=os.getenv("DB_NAME"),
        )
    except asyncpg.InvalidPasswordError:
        raise HTTPException(status_code=500, detail="Database authentication failed.")
    except asyncpg.CannotConnectNowError:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
