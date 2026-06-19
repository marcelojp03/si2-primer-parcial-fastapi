-- Migration 008: foto_url para vehiculos

ALTER TABLE auxilio_mecanico.vehiculos
  ADD COLUMN IF NOT EXISTS foto_url VARCHAR(500) NULL;

COMMENT ON COLUMN auxilio_mecanico.vehiculos.foto_url IS 'URL de la foto del vehiculo (almacenada en S3)';
