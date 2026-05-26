from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("nombre", String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
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
    workshops = relationship("Workshop", back_populates="tenant")
    users = relationship("User", back_populates="tenant", foreign_keys="User.tenant_id")
