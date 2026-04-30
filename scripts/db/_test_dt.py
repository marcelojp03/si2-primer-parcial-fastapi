"""Test datetime encoding con asyncpg."""
import asyncio, asyncpg, os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()

async def t():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
    c = await asyncpg.connect(url)

    # Test 1: naive
    naive_dt = datetime(2026, 3, 30, 18, 0, 0)
    try:
        await c.fetchval("SELECT $1::timestamp", naive_dt)
        print("naive_dt -> OK")
    except Exception as e:
        print(f"naive_dt -> ERROR: {e}")

    # Test 2: aware UTC
    aware_dt = datetime(2026, 3, 30, 18, 0, 0, tzinfo=timezone.utc)
    try:
        await c.fetchval("SELECT $1::timestamp", aware_dt)
        print("aware_dt -> OK")
    except Exception as e:
        print(f"aware_dt -> ERROR: {e}")

    # Test 3: naive utcnow
    naive_utcnow = datetime.utcnow()
    try:
        await c.fetchval("SELECT $1::timestamp", naive_utcnow)
        print("naive_utcnow -> OK")
    except Exception as e:
        print(f"naive_utcnow -> ERROR: {e}")

    await c.close()

asyncio.run(t())
