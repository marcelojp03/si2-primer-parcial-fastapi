-- Migration 010: quotation fields en candidatos (para aceptar+cotizar en un paso)

ALTER TABLE auxilio_mecanico.candidatos_taller_incidente
  ADD COLUMN IF NOT EXISTS costo_cotizacion NUMERIC(10,2) NULL,
  ADD COLUMN IF NOT EXISTS tiempo_cotizacion_min INTEGER NULL,
  ADD COLUMN IF NOT EXISTS descripcion_cotizacion TEXT NULL;

COMMENT ON COLUMN auxilio_mecanico.candidatos_taller_incidente.costo_cotizacion IS 'Costo estimado de la cotizacion enviada al aceptar';
COMMENT ON COLUMN auxilio_mecanico.candidatos_taller_incidente.tiempo_cotizacion_min IS 'Tiempo estimado de reparacion en minutos';
COMMENT ON COLUMN auxilio_mecanico.candidatos_taller_incidente.descripcion_cotizacion IS 'Descripcion del trabajo a realizar';
