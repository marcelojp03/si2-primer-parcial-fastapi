from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class User(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column("rol", String(30), nullable=False)
    full_name: Mapped[str] = mapped_column("nombre_completo", String(150), nullable=False)
    ci: Mapped[str | None] = mapped_column(String(30))
    phone: Mapped[str | None] = mapped_column("telefono", String(30))
    email: Mapped[str] = mapped_column(
        "correo_electronico", String(150), nullable=False, unique=True
    )
    password_hash: Mapped[str] = mapped_column("contrasena_hash", String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        "estado", String(30), nullable=False, server_default="ACTIVO"
    )
    tenant_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.tenants.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    is_platform_admin: Mapped[bool] = mapped_column(
        "es_admin_plataforma", Boolean, nullable=False, server_default="false"
    )
    fcm_token: Mapped[str | None] = mapped_column(
        "fcm_token", String(255), nullable=True
    )
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[str] = mapped_column(
        "fecha_actualizacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])
    workshop = relationship("Workshop", back_populates="admin_user", uselist=False)
    vehicles = relationship("Vehicle", back_populates="user")
    incidents = relationship("Incident", back_populates="client_user")
