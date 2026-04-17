from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class Rating(Base):
    __tablename__ = "calificaciones"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    service_assignment_id: Mapped[int] = mapped_column(
        "asignacion_servicio_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.asignaciones_servicio.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    client_user_id: Mapped[int] = mapped_column(
        "cliente_usuario_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.usuarios.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    score: Mapped[int] = mapped_column("puntuacion", Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column("comentario", String(255))
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    assignment = relationship("ServiceAssignment", back_populates="rating")
    client_user = relationship("User")
