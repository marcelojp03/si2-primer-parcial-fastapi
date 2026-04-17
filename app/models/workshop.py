from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class Workshop(Base):
    __tablename__ = "talleres"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_user_id: Mapped[int] = mapped_column(
        "administrador_usuario_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.usuarios.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    name: Mapped[str] = mapped_column("nombre", String(150), nullable=False)
    description: Mapped[str | None] = mapped_column("descripcion", String(255))
    phone: Mapped[str | None] = mapped_column("telefono", String(30))
    email: Mapped[str | None] = mapped_column("correo_electronico", String(150))
    address: Mapped[str | None] = mapped_column("direccion", String(255))
    latitude: Mapped[float | None] = mapped_column("latitud", Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column("longitud", Numeric(9, 6))
    has_tow: Mapped[bool] = mapped_column(
        "tiene_remolque", Boolean, nullable=False, server_default="false"
    )
    is_24_hours: Mapped[bool] = mapped_column(
        "atiende_24_horas", Boolean, nullable=False, server_default="false"
    )
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
    admin_user = relationship("User", back_populates="workshop")
    schedules = relationship(
        "WorkshopSchedule", back_populates="workshop", cascade="all, delete-orphan"
    )
    specialties = relationship(
        "WorkshopSpecialty", back_populates="workshop", cascade="all, delete-orphan"
    )
    technicians = relationship(
        "Technician", back_populates="workshop", cascade="all, delete-orphan"
    )
