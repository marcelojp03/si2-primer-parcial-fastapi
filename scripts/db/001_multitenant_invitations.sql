-- =============================================================================
-- Migration 001: Multi-tenant + Invitaciones + Reputación
-- Fecha: 2026-05-26
-- Descripción:
--   - CREATE TABLE tenants
--   - talleres: tenant_id FK, columnas de reputación
--   - usuarios: tenant_id (nullable), es_admin_plataforma flag
--   - asignaciones_servicio: tenant_id FK
--   - incidentes: uuid_cliente UUID UNIQUE (idempotencia offline)
--   - candidatos_taller_incidente: fecha_limite_respuesta, tiempo_respuesta_segundos
--   - estados_incidente: seed BUSCANDO_TALLER (orden 9)
-- =============================================================================

SET search_path TO auxilio_mecanico;

-- ---------------------------------------------------------------------------
-- 1. Tabla tenants
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auxilio_mecanico.tenants (
    id                  BIGSERIAL PRIMARY KEY,
    nombre              VARCHAR(150) NOT NULL,
    slug                VARCHAR(80)  NOT NULL,
    estado              VARCHAR(30)  NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion      TIMESTAMP    NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tenants_slug   UNIQUE (slug),
    CONSTRAINT chk_tenants_estado CHECK (estado IN ('ACTIVO','INACTIVO','SUSPENDIDO'))
);

-- Seed: tenant por defecto para backfill de talleres existentes
INSERT INTO auxilio_mecanico.tenants (nombre, slug, estado)
VALUES ('Taller Principal', 'default', 'ACTIVO')
ON CONFLICT (slug) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 2. talleres: tenant_id + reputación
-- ---------------------------------------------------------------------------
ALTER TABLE auxilio_mecanico.talleres
    ADD COLUMN IF NOT EXISTS tenant_id             BIGINT,
    ADD COLUMN IF NOT EXISTS puntaje_reputacion    NUMERIC(5,2) NOT NULL DEFAULT 100,
    ADD COLUMN IF NOT EXISTS invitaciones_recibidas    INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS invitaciones_respondidas  INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS invitaciones_ignoradas    INTEGER NOT NULL DEFAULT 0;

-- FK (agrega restricción solo si no existe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_talleres_tenant_id'
          AND table_schema = 'auxilio_mecanico'
    ) THEN
        ALTER TABLE auxilio_mecanico.talleres
            ADD CONSTRAINT fk_talleres_tenant_id
            FOREIGN KEY (tenant_id)
            REFERENCES auxilio_mecanico.tenants(id)
            ON UPDATE CASCADE ON DELETE RESTRICT;
    END IF;
END$$;

-- Backfill: asignar tenant por defecto a todos los talleres existentes
UPDATE auxilio_mecanico.talleres
SET tenant_id = (SELECT id FROM auxilio_mecanico.tenants WHERE slug = 'default')
WHERE tenant_id IS NULL;

-- Ahora hacer NOT NULL
ALTER TABLE auxilio_mecanico.talleres
    ALTER COLUMN tenant_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_talleres_tenant_id
    ON auxilio_mecanico.talleres (tenant_id);

-- ---------------------------------------------------------------------------
-- 3. usuarios: tenant_id (nullable) + es_admin_plataforma
-- ---------------------------------------------------------------------------
ALTER TABLE auxilio_mecanico.usuarios
    ADD COLUMN IF NOT EXISTS tenant_id            BIGINT,
    ADD COLUMN IF NOT EXISTS es_admin_plataforma  BOOLEAN NOT NULL DEFAULT FALSE;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_usuarios_tenant_id'
          AND table_schema = 'auxilio_mecanico'
    ) THEN
        ALTER TABLE auxilio_mecanico.usuarios
            ADD CONSTRAINT fk_usuarios_tenant_id
            FOREIGN KEY (tenant_id)
            REFERENCES auxilio_mecanico.tenants(id)
            ON UPDATE CASCADE ON DELETE SET NULL;
    END IF;
END$$;

-- Backfill: ADMIN_TALLER recibe el tenant del taller que administra
UPDATE auxilio_mecanico.usuarios u
SET tenant_id = t.tenant_id
FROM auxilio_mecanico.talleres t
WHERE t.administrador_usuario_id = u.id
  AND u.rol = 'ADMIN_TALLER'
  AND u.tenant_id IS NULL;

-- ---------------------------------------------------------------------------
-- 4. asignaciones_servicio: tenant_id
-- ---------------------------------------------------------------------------
ALTER TABLE auxilio_mecanico.asignaciones_servicio
    ADD COLUMN IF NOT EXISTS tenant_id BIGINT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_asignaciones_tenant_id'
          AND table_schema = 'auxilio_mecanico'
    ) THEN
        ALTER TABLE auxilio_mecanico.asignaciones_servicio
            ADD CONSTRAINT fk_asignaciones_tenant_id
            FOREIGN KEY (tenant_id)
            REFERENCES auxilio_mecanico.tenants(id)
            ON UPDATE CASCADE ON DELETE RESTRICT;
    END IF;
END$$;

-- Backfill: asignar tenant a partir del taller de la asignación
UPDATE auxilio_mecanico.asignaciones_servicio a
SET tenant_id = t.tenant_id
FROM auxilio_mecanico.talleres t
WHERE a.taller_id = t.id
  AND a.tenant_id IS NULL;

ALTER TABLE auxilio_mecanico.asignaciones_servicio
    ALTER COLUMN tenant_id SET NOT NULL;

-- ---------------------------------------------------------------------------
-- 5. incidentes: uuid_cliente (idempotencia offline)
-- ---------------------------------------------------------------------------
ALTER TABLE auxilio_mecanico.incidentes
    ADD COLUMN IF NOT EXISTS uuid_cliente UUID;

CREATE UNIQUE INDEX IF NOT EXISTS uq_incidentes_uuid_cliente
    ON auxilio_mecanico.incidentes (uuid_cliente)
    WHERE uuid_cliente IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 6. candidatos_taller_incidente: TTL de invitación + tiempo de respuesta
-- ---------------------------------------------------------------------------
ALTER TABLE auxilio_mecanico.candidatos_taller_incidente
    ADD COLUMN IF NOT EXISTS fecha_limite_respuesta      TIMESTAMP,
    ADD COLUMN IF NOT EXISTS tiempo_respuesta_segundos   INTEGER;

-- ---------------------------------------------------------------------------
-- 7. Seed estado BUSCANDO_TALLER
-- ---------------------------------------------------------------------------
INSERT INTO auxilio_mecanico.estados_incidente (nombre, descripcion, orden)
VALUES ('BUSCANDO_TALLER', 'El sistema está buscando un taller disponible', 9)
ON CONFLICT (nombre) DO NOTHING;
