-- Migration 009: user_id en tecnicos + role TECNICO

ALTER TABLE auxilio_mecanico.tecnicos
  ADD COLUMN IF NOT EXISTS usuario_id BIGINT NULL REFERENCES auxilio_mecanico.usuarios(id)
    ON UPDATE CASCADE ON DELETE SET NULL;

COMMENT ON COLUMN auxilio_mecanico.tecnicos.usuario_id IS 'Vinculacion del tecnico con un usuario del sistema para login';
