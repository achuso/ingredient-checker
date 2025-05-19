import asyncpg
import os
from fastapi import HTTPException

class Database:
    def __init__(self):
        self._conn = None

    async def connect(self):
        try:
            self._conn = await asyncpg.connect(
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

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def fetchrow(self, query: str, *args):
        try:
            return await self._conn.fetchrow(query, *args)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database fetchrow error: {str(e)}")

    async def fetch(self, query: str, *args):
        try:
            return await self._conn.fetch(query, *args)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database fetch error: {str(e)}")

    async def execute(self, query: str, *args):
        try:
            return await self._conn.execute(query, *args)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database execute error: {str(e)}")
