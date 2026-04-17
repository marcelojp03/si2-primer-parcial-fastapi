from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class Technician(Base):
    __tablename__ = "tecnicos"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workshop_id: Mapped[int] = mapped_column(
        "taller_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.talleres.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column("nombre_completo", String(150), nullable=False)
    ci: Mapped[str | None] = mapped_column(String(30))
    phone: Mapped[str | None] = mapped_column("telefono", String(30))
    availability_status: Mapped[str] = mapped_column(
        "estado_disponibilidad", String(30), nullable=False, server_default="DISPONIBLE"
    )
    notes: Mapped[str | None] = mapped_column("observaciones", String(255))
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[str] = mapped_column(
        "fecha_actualizacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    workshop = relationship("Workshop", back_populates="technicians")
    specialties = relationship(
        "TechnicianSpecialty", back_populates="technician", cascade="all, delete-orphan"
    )
