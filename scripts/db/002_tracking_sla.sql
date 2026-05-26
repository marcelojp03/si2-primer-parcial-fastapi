-- =============================================================================
-- Migration 002: Tracking de Ubicación + SLA de Tipos de Incidente
-- Fecha: 2026-05-26
-- Descripción:
--   - CREATE TABLE seguimiento_ubicacion_incidente
--   - tipos_incidente: sla_minutos INTEGER con valores por defecto
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Tabla de tracking de ubicación
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auxilio_mecanico.seguimiento_ubicacion_incidente (
    id              BIGSERIAL PRIMARY KEY,
    incidente_id    BIGINT    NOT NULL,
    latitud         NUMERIC(9,6) NOT NULL,
    longitud        NUMERIC(9,6) NOT NULL,
    registrado_en   TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_seguimiento_incidente
        FOREIGN KEY (incidente_id)
        REFERENCES auxilio_mecanico.incidentes(id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_seguimiento_incidente_id
    ON auxilio_mecanico.seguimiento_ubicacion_incidente (incidente_id);

CREATE INDEX IF NOT EXISTS idx_seguimiento_registrado_en
    ON auxilio_mecanico.seguimiento_ubicacion_incidente (incidente_id, registrado_en);

-- ---------------------------------------------------------------------------
-- 2. tipos_incidente: columna sla_minutos
-- ---------------------------------------------------------------------------
ALTER TABLE auxilio_mecanico.tipos_incidente
    ADD COLUMN IF NOT EXISTS sla_minutos INTEGER;

-- Seed SLA por defecto (minutos)
UPDATE auxilio_mecanico.tipos_incidente SET sla_minutos = 30 WHERE nombre = 'BATERIA';
UPDATE auxilio_mecanico.tipos_incidente SET sla_minutos = 20 WHERE nombre = 'LLANTA';
UPDATE auxilio_mecanico.tipos_incidente SET sla_minutos = 45 WHERE nombre = 'CHOQUE';
UPDATE auxilio_mecanico.tipos_incidente SET sla_minutos = 60 WHERE nombre = 'MOTOR';
UPDATE auxilio_mecanico.tipos_incidente SET sla_minutos = 25 WHERE nombre = 'LLAVE';
UPDATE auxilio_mecanico.tipos_incidente SET sla_minutos = 45 WHERE nombre = 'INCIERTO';
