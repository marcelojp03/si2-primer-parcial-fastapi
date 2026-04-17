from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class WorkshopSpecialty(Base):
    __tablename__ = "taller_especialidades"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workshop_id: Mapped[int] = mapped_column(
        "taller_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.talleres.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    specialty_id: Mapped[int] = mapped_column(
        "especialidad_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.especialidades.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    workshop = relationship("Workshop", back_populates="specialties")
    specialty = relationship("Specialty")
