import os
import asyncpg
from fastapi import HTTPException
from typing import AsyncGenerator


class Database:
    """
    Wrapper around asyncpg.Connection. Call `connect()` at startup,
    and reuse the same connection for all queries.
    """

    def __init__(self):
        self._conn: asyncpg.Connection | None = None

    async def connect(self) -> None:
        """
        Establish a connection to the PostgreSQL database using environment variables.
        """
        if self._conn:  # already connected
            return

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

    async def close(self) -> None:
        """
        Close the underlying connection, if it exists.
        """
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def fetchrow(self, query: str, *args) -> dict | None:
        """
        Execute a query that returns a single row.
        """
        if not self._conn:
            await self.connect()
        try:
            return await self._conn.fetchrow(query, *args)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database fetchrow error: {str(e)}")

    async def fetch(self, query: str, *args) -> list[dict]:
        """
        Execute a query that returns multiple rows.
        """
        if not self._conn:
            await self.connect()
        try:
            return await self._conn.fetch(query, *args)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database fetch error: {str(e)}")

    async def execute(self, query: str, *args) -> str:
        """
        Execute an INSERT/UPDATE/DELETE or any SQL that does not return rows.
        Returns the status string.
        """
        if not self._conn:
            await self.connect()
        try:
            return await self._conn.execute(query, *args)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database execute error: {str(e)}")


# Instantiate a single, shared Database object for the entire app
db = Database()


async def get_db() -> AsyncGenerator[Database, None]:
    """
    FastAPI dependency: yields the shared Database instance.
    Ensures that the connection is open before yielding.
    """
    # Ensure the connection is open
    await db.connect()
    try:
        yield db
    finally:
        # NOTE: we do NOT close the connection here, because
        # we want to reuse it across requests. Closing should
        # only happen on application shutdown if desired.
        pass
