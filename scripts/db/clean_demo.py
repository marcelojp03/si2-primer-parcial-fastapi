"""Elimina todos los datos demo del seed para permitir re-ejecución."""
import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()
S = "auxilio_mecanico"

TABLES = [
    "calificaciones",
    "pagos",
    "asignaciones_servicio",
    "candidatos_taller_incidente",
    "historial_estados_incidente",
    "evidencias_incidente",
    "analisis_ia_incidente",
    "incidentes",
    "vehiculos",
    "tecnico_especialidades",
    "tecnicos",
    "taller_especialidades",
    "horarios_taller",
    "talleres",
    "usuarios",
]


async def clean() -> None:
    url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        for t in TABLES:
            await conn.execute(f"DELETE FROM {S}.{t}")
            print(f"  ✓ {t}")
        print("\nLimpieza completa. Puedes volver a ejecutar seed_demo.py")
    finally:
        await conn.close()


asyncio.run(clean())
