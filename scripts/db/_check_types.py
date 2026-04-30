import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv()
async def t():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
    c = await asyncpg.connect(url)
    rows = await c.fetch("""
        SELECT column_name, data_type, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'auxilio_mecanico'
          AND table_name = 'incidentes'
          AND column_name LIKE 'fecha%'
        ORDER BY ordinal_position
    """)
    for r in rows:
        print(r['column_name'], '->', r['data_type'])
    await c.close()
asyncio.run(t())
