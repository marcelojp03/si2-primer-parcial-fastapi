-- Migration 007: tenant_id nullable en incidentes
-- Los incidentes de CLIENTE no tienen tenant propio, pero una vez que un taller
-- del tenant X se asigna, el incidente queda vinculado a ese tenant.

ALTER TABLE auxilio_mecanico.incidentes
  ADD COLUMN IF NOT EXISTS tenant_id BIGINT NULL REFERENCES auxilio_mecanico.tenants(id)
    ON UPDATE CASCADE ON DELETE SET NULL;

COMMENT ON COLUMN auxilio_mecanico.incidentes.tenant_id
  IS 'Tenant al que pertenece el incidente (nullable, se llena al asignar taller).';
