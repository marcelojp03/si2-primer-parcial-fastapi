-- Seed: Datos de prueba para tracking GPS tecnico-cliente
-- Crea: usuario TECNICO, perfil de tecnico, vehiculo, incidente, asignacion
-- Requiere: tenant 1 existente, taller 39 existente (AutoService Cruz del Sur)
-- La contrasena para ambos usuarios es: Auxilio2026!
-- El hash bcrypt de "Auxilio2026!" debe generarse con el backend o con:
-- python -c "import bcrypt; print(bcrypt.hashpw(b'Auxilio2026!', bcrypt.gensalt()).decode())"

DO $$
DECLARE
    v_tenant_id BIGINT := 1;
    v_taller_id BIGINT := 39;
    v_cliente_id BIGINT;
    v_tecnico_user_id BIGINT;
    v_tecnico_id BIGINT;
    v_vehiculo_id BIGINT;
    v_incidente_id BIGINT;
    v_hash VARCHAR(255) := '$2b$12$S2drxc/t6WhNFsQHJNJWXOV8pn5Zaj19rVp24kPdGjyWMOJ5FtKoS';
BEGIN

    -- 1. Cliente de prueba
    INSERT INTO auxilio_mecanico.usuarios (rol, nombre_completo, correo_electronico, contrasena_hash, tenant_id)
    VALUES ('CLIENTE', 'Cliente Demo', 'cliente@demo.com', v_hash, v_tenant_id)
    RETURNING id INTO v_cliente_id;

    -- 2. Tecnico user
    INSERT INTO auxilio_mecanico.usuarios (rol, nombre_completo, correo_electronico, contrasena_hash, tenant_id)
    VALUES ('TECNICO', 'Tecnico Demo', 'tecnico@demo.com', v_hash, v_tenant_id)
    RETURNING id INTO v_tecnico_user_id;

    -- 3. Tecnico profile
    INSERT INTO auxilio_mecanico.tecnicos (taller_id, nombre_completo, usuario_id, estado_disponibilidad)
    VALUES (v_taller_id, 'Tecnico Demo', v_tecnico_user_id, 'DISPONIBLE')
    RETURNING id INTO v_tecnico_id;

    -- 4. Vehiculo
    INSERT INTO auxilio_mecanico.vehiculos (usuario_id, placa, marca, modelo, anio_fabricacion, color)
    VALUES (v_cliente_id, 'ABC-123', 'Toyota', 'Corolla', 2020, 'Blanco')
    RETURNING id INTO v_vehiculo_id;

    -- 5. Incidente
    INSERT INTO auxilio_mecanico.incidentes (cliente_usuario_id, vehiculo_id, titulo, descripcion_texto,
        latitud, longitud, requiere_remolque, modalidad_servicio, estado_incidente_id)
    VALUES (v_cliente_id, v_vehiculo_id, 'Auto no enciende', 'El motor no arranca después de varios intentos',
        -17.7833, -63.1822, false, 'A_DOMICILIO', 1)
    RETURNING id INTO v_incidente_id;

    -- 6. Asignacion con tecnico
    INSERT INTO auxilio_mecanico.asignaciones_servicio (incidente_id, taller_id, tenant_id, tecnico_id, estado_asignacion)
    VALUES (v_incidente_id, v_taller_id, v_tenant_id, v_tecnico_id, 'ASIGNADO');

    RAISE NOTICE 'Datos creados:';
    RAISE NOTICE '  Cliente: client@test.com / Auxilio2026!';
    RAISE NOTICE '  Tecnico: tech@test.com / Auxilio2026!';
    RAISE NOTICE '  Incidente ID: %', v_incidente_id;
    RAISE NOTICE '  Tecnico ID: %', v_tecnico_id;

END $$;
