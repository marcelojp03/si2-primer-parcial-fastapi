"""Create schema and all tables from SQLAlchemy models (used in CI)."""

import asyncio

from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.models import *  # noqa: F401,F403


async def main() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS auxilio_mecanico"))
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Schema and tables created successfully.")


if __name__ == "__main__":
    asyncio.run(main())
