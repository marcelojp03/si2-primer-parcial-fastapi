-- Migration 005: Modalidad de servicio (A_DOMICILIO | CLIENTE_VE_TALLER)

ALTER TABLE auxilio_mecanico.incidentes
  ADD COLUMN IF NOT EXISTS modalidad_servicio VARCHAR(20) NOT NULL DEFAULT 'A_DOMICILIO';

COMMENT ON COLUMN auxilio_mecanico.incidentes.modalidad_servicio
  IS 'A_DOMICILIO = el auxilio va al cliente (tracking del tecnico). CLIENTE_VE_TALLER = el cliente lleva el vehiculo al taller (ruta + ETA).';
