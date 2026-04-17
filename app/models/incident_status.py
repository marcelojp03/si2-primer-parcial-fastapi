from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class IncidentStatus(Base):
    __tablename__ = "estados_incidente"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("nombre", String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column("descripcion", String(255))
    sort_order: Mapped[int] = mapped_column("orden", Integer, nullable=False, unique=True)
    status: Mapped[str] = mapped_column("estado", String(30), nullable=False, server_default="ACTIVO")
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[str] = mapped_column(
        "fecha_actualizacion", DateTime, nullable=False, server_default=func.now()
    )
