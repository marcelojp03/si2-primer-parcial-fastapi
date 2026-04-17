from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class Vehicle(Base):
    __tablename__ = "vehiculos"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        "usuario_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.usuarios.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    plate: Mapped[str] = mapped_column("placa", String(20), nullable=False, unique=True)
    brand: Mapped[str] = mapped_column("marca", String(80), nullable=False)
    model: Mapped[str] = mapped_column("modelo", String(80), nullable=False)
    manufacture_year: Mapped[int | None] = mapped_column("anio_fabricacion", Integer)
    color: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column("observaciones", String(255))
    status: Mapped[str] = mapped_column(
        "estado", String(30), nullable=False, server_default="ACTIVO"
    )
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[str] = mapped_column(
        "fecha_actualizacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="vehicles")
    incidents = relationship("Incident", back_populates="vehicle")
