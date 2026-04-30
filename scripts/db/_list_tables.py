import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv()
async def t():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
    c = await asyncpg.connect(url)
    rows = await c.fetch("SELECT tablename FROM pg_tables WHERE schemaname='auxilio_mecanico' ORDER BY tablename")
    for r in rows:
        print(r['tablename'])
    await c.close()
asyncio.run(t())
