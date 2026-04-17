import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory

logger = logging.getLogger(__name__)

SEED_INCIDENT_TYPES = [
    ("BATERIA", "Problemas relacionados con bateria o sistema electrico basico"),
    ("LLANTA", "Pinchazo, reventon o problema de llantas"),
    ("CHOQUE", "Accidente o colision leve"),
    ("MOTOR", "Problema mecanico de motor"),
    ("LLAVE", "Llave perdida, olvidada o problema de apertura"),
    ("INCIERTO", "Caso ambiguo o no clasificado"),
]

SEED_INCIDENT_STATUSES = [
    ("PENDIENTE", "Incidente reportado y pendiente de procesamiento", 1),
    ("NOTIFICADO", "Talleres candidatos ya fueron notificados", 2),
    ("ACEPTADO", "Un taller acepto la solicitud", 3),
    ("EN_PROCESO", "La atencion del servicio esta en curso", 4),
    ("ATENDIDO", "El incidente fue atendido", 5),
    ("CANCELADO", "El incidente fue cancelado", 6),
    ("PENDIENTE_PAGO", "El servicio fue atendido y espera pago", 7),
    ("PAGADO", "El pago fue confirmado", 8),
]

SEED_SPECIALTIES = [
    ("BATERIA", "Atencion de problemas de bateria y sistema electrico"),
    ("LLANTAS", "Atencion de pinchazos, cambio o reparacion de llantas"),
    ("MOTOR", "Atencion de fallas de motor"),
    ("SUSPENSION", "Atencion de problemas de suspension"),
    ("CERRAJERIA_VEHICULAR", "Apertura o asistencia por llaves"),
    ("REMOLQUE", "Traslado del vehiculo mediante remolque"),
]


async def create_schema(session: AsyncSession) -> None:
    await session.execute(text("CREATE SCHEMA IF NOT EXISTS auxilio_mecanico"))
    await session.commit()


async def seed_incident_types(session: AsyncSession) -> None:
    for name, description in SEED_INCIDENT_TYPES:
        await session.execute(
            text(
                """
                INSERT INTO auxilio_mecanico.tipos_incidente (nombre, descripcion)
                VALUES (:name, :description)
                ON CONFLICT (nombre) DO NOTHING
                """
            ),
            {"name": name, "description": description},
        )
    await session.commit()


async def seed_incident_statuses(session: AsyncSession) -> None:
    for name, description, order in SEED_INCIDENT_STATUSES:
        await session.execute(
            text(
                """
                INSERT INTO auxilio_mecanico.estados_incidente (nombre, descripcion, orden)
                VALUES (:name, :description, :order)
                ON CONFLICT (nombre) DO NOTHING
                """
            ),
            {"name": name, "description": description, "order": order},
        )
    await session.commit()


async def seed_specialties(session: AsyncSession) -> None:
    for name, description in SEED_SPECIALTIES:
        await session.execute(
            text(
                """
                INSERT INTO auxilio_mecanico.especialidades (nombre, descripcion)
                VALUES (:name, :description)
                ON CONFLICT (nombre) DO NOTHING
                """
            ),
            {"name": name, "description": description},
        )
    await session.commit()


async def _already_seeded(session: AsyncSession) -> bool:
    result = await session.execute(text("SELECT 1 FROM auxilio_mecanico.tipos_incidente LIMIT 1"))
    return result.scalar() is not None


async def init_db() -> None:
    async with async_session_factory() as session:
        await create_schema(session)
        try:
            if await _already_seeded(session):
                logger.info("Database already seeded - skipping")
                return
        except Exception:
            pass  # table doesn't exist yet, will seed
        await seed_incident_types(session)
        await seed_incident_statuses(session)
        await seed_specialties(session)
        logger.info("Database seeded successfully")
