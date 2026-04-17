-- =========================================================
-- MODELO LOGICO - AUXILIO MECANICO
-- PostgreSQL
-- =========================================================

create schema if not exists auxilio_mecanico;
set search_path to auxilio_mecanico, public;

-- =========================================================
-- FUNCION GENERICA PARA fecha_actualizacion
-- =========================================================
create or replace function actualizar_fecha_actualizacion()
returns trigger
language plpgsql
as $$
begin
    new.fecha_actualizacion = now();
    return new;
end;
$$;

-- =========================================================
-- TABLAS PRINCIPALES
-- =========================================================

create table if not exists usuarios (
    id bigint generated always as identity primary key,
    rol varchar(30) not null,
    nombre_completo varchar(150) not null,
    ci varchar(30),
    telefono varchar(30),
    correo_electronico varchar(150) not null,
    contrasena_hash varchar(255) not null,
    estado varchar(30) not null default 'ACTIVO',
    fecha_creacion timestamp not null default now(),
    fecha_actualizacion timestamp not null default now(),

    constraint uq_usuarios_correo unique (correo_electronico),
    constraint chk_usuarios_rol
        check (rol in ('CLIENTE', 'ADMIN_TALLER', 'SUPERADMIN')),
    constraint chk_usuarios_estado
        check (estado in ('ACTIVO', 'INACTIVO', 'SUSPENDIDO'))
);

create table if not exists talleres (
    id bigint generated always as identity primary key,
    administrador_usuario_id bigint not null,
    nombre varchar(150) not null,
    descripcion varchar(255),
    telefono varchar(30),
    correo_electronico varchar(150),
    direccion varchar(255),
    latitud numeric(9,6),
    longitud numeric(9,6),
    tiene_remolque boolean not null default false,
    atiende_24_horas boolean not null default false,
    estado varchar(30) not null default 'ACTIVO',
    fecha_creacion timestamp not null default now(),
    fecha_actualizacion timestamp not null default now(),

    constraint uq_talleres_admin unique (administrador_usuario_id),
    constraint fk_talleres_admin
        foreign key (administrador_usuario_id)
        references usuarios(id)
        on update cascade
        on delete restrict,
    constraint chk_talleres_estado
        check (estado in ('ACTIVO', 'INACTIVO'))
);

create table if not exists horarios_taller (
    id bigint generated always as identity primary key,
    taller_id bigint not null,
    dia_semana varchar(20) not null,
    hora_inicio time not null,
    hora_fin time not null,
    activo boolean not null default true,
    fecha_creacion timestamp not null default now(),

    constraint fk_horarios_taller_taller
        foreign key (taller_id)
        references talleres(id)
        on update cascade
        on delete cascade,
    constraint uq_horarios_taller unique (taller_id, dia_semana, hora_inicio, hora_fin),
    constraint chk_horarios_dia_semana
        check (dia_semana in (
            'LUNES', 'MARTES', 'MIERCOLES', 'JUEVES',
            'VIERNES', 'SABADO', 'DOMINGO'
        )),
    constraint chk_horarios_rango
        check (hora_fin > hora_inicio)
);

create table if not exists vehiculos (
    id bigint generated always as identity primary key,
    usuario_id bigint not null,
    placa varchar(20) not null,
    marca varchar(80) not null,
    modelo varchar(80) not null,
    anio_fabricacion integer,
    color varchar(50),
    observaciones varchar(255),
    estado varchar(30) not null default 'ACTIVO',
    fecha_creacion timestamp not null default now(),
    fecha_actualizacion timestamp not null default now(),

    constraint uq_vehiculos_placa unique (placa),
    constraint fk_vehiculos_usuario
        foreign key (usuario_id)
        references usuarios(id)
        on update cascade
        on delete restrict,
    constraint chk_vehiculos_estado
        check (estado in ('ACTIVO', 'INACTIVO')),
    constraint chk_vehiculos_anio
        check (anio_fabricacion is null or anio_fabricacion between 1950 and 2100)
);

create table if not exists especialidades (
    id bigint generated always as identity primary key,
    nombre varchar(100) not null,
    descripcion varchar(255),
    estado varchar(30) not null default 'ACTIVO',
    fecha_creacion timestamp not null default now(),
    fecha_actualizacion timestamp not null default now(),

    constraint uq_especialidades_nombre unique (nombre),
    constraint chk_especialidades_estado
        check (estado in ('ACTIVO', 'INACTIVO'))
);

create table if not exists taller_especialidades (
    id bigint generated always as identity primary key,
    taller_id bigint not null,
    especialidad_id bigint not null,
    fecha_creacion timestamp not null default now(),

    constraint uq_taller_especialidad unique (taller_id, especialidad_id),
    constraint fk_taller_especialidades_taller
        foreign key (taller_id)
        references talleres(id)
        on update cascade
        on delete cascade,
    constraint fk_taller_especialidades_especialidad
        foreign key (especialidad_id)
        references especialidades(id)
        on update cascade
        on delete restrict
);

create table if not exists tecnicos (
    id bigint generated always as identity primary key,
    taller_id bigint not null,
    nombre_completo varchar(150) not null,
    ci varchar(30),
    telefono varchar(30),
    estado_disponibilidad varchar(30) not null default 'DISPONIBLE',
    observaciones varchar(255),
    fecha_creacion timestamp not null default now(),
    fecha_actualizacion timestamp not null default now(),

    constraint fk_tecnicos_taller
        foreign key (taller_id)
        references talleres(id)
        on update cascade
        on delete cascade,
    constraint chk_tecnicos_estado_disponibilidad
        check (estado_disponibilidad in ('DISPONIBLE', 'OCUPADO', 'INACTIVO'))
);

create table if not exists tecnico_especialidades (
    id bigint generated always as identity primary key,
    tecnico_id bigint not null,
    especialidad_id bigint not null,
    fecha_creacion timestamp not null default now(),

    constraint uq_tecnico_especialidad unique (tecnico_id, especialidad_id),
    constraint fk_tecnico_especialidades_tecnico
        foreign key (tecnico_id)
        references tecnicos(id)
        on update cascade
        on delete cascade,
    constraint fk_tecnico_especialidades_especialidad
        foreign key (especialidad_id)
        references especialidades(id)
        on update cascade
        on delete restrict
);

create table if not exists tipos_incidente (
    id bigint generated always as identity primary key,
    nombre varchar(100) not null,
    descripcion varchar(255),
    estado varchar(30) not null default 'ACTIVO',
    fecha_creacion timestamp not null default now(),
    fecha_actualizacion timestamp not null default now(),

    constraint uq_tipos_incidente_nombre unique (nombre),
    constraint chk_tipos_incidente_estado
        check (estado in ('ACTIVO', 'INACTIVO'))
);

create table if not exists estados_incidente (
    id bigint generated always as identity primary key,
    nombre varchar(100) not null,
    descripcion varchar(255),
    orden integer not null,
    estado varchar(30) not null default 'ACTIVO',
    fecha_creacion timestamp not null default now(),
    fecha_actualizacion timestamp not null default now(),

    constraint uq_estados_incidente_nombre unique (nombre),
    constraint uq_estados_incidente_orden unique (orden),
    constraint chk_estados_incidente_estado
        check (estado in ('ACTIVO', 'INACTIVO')),
    constraint chk_estados_incidente_orden
        check (orden > 0)
);

create table if not exists incidentes (
    id bigint generated always as identity primary key,
    cliente_usuario_id bigint not null,
    vehiculo_id bigint not null,
    tipo_incidente_id bigint,
    estado_incidente_id bigint not null,
    titulo varchar(150) not null,
    descripcion_texto text,
    direccion_referencia varchar(255),
    latitud numeric(9,6),
    longitud numeric(9,6),
    nivel_prioridad varchar(20),
    requiere_remolque boolean not null default false,
    fecha_solicitud timestamp not null default now(),
    fecha_aceptacion timestamp,
    fecha_inicio_atencion timestamp,
    fecha_finalizacion timestamp,
    fecha_cancelacion timestamp,
    fecha_creacion timestamp not null default now(),
    fecha_actualizacion timestamp not null default now(),

    constraint fk_incidentes_cliente
        foreign key (cliente_usuario_id)
        references usuarios(id)
        on update cascade
        on delete restrict,
    constraint fk_incidentes_vehiculo
        foreign key (vehiculo_id)
        references vehiculos(id)
        on update cascade
        on delete restrict,
    constraint fk_incidentes_tipo
        foreign key (tipo_incidente_id)
        references tipos_incidente(id)
        on update cascade
        on delete set null,
    constraint fk_incidentes_estado
        foreign key (estado_incidente_id)
        references estados_incidente(id)
        on update cascade
        on delete restrict,
    constraint chk_incidentes_prioridad
        check (
            nivel_prioridad is null
            or nivel_prioridad in ('BAJA', 'MEDIA', 'ALTA', 'CRITICA', 'INCIERTA')
        )
);

create table if not exists evidencias_incidente (
    id bigint generated always as identity primary key,
    incidente_id bigint not null,
    tipo_evidencia varchar(20) not null,
    url_archivo varchar(255),
    clave_archivo varchar(255),
    tipo_mime varchar(100),
    nombre_archivo varchar(150),
    tamano_archivo bigint,
    fecha_carga timestamp not null default now(),

    constraint fk_evidencias_incidente
        foreign key (incidente_id)
        references incidentes(id)
        on update cascade
        on delete cascade,
    constraint chk_evidencias_tipo
        check (tipo_evidencia in ('IMAGEN', 'AUDIO', 'VIDEO', 'DOCUMENTO')),
    constraint chk_evidencias_tamano
        check (tamano_archivo is null or tamano_archivo >= 0)
);

create table if not exists analisis_ia_incidente (
    id bigint generated always as identity primary key,
    incidente_id bigint not null,
    audio_transcrito text,
    resumen_generado text,
    tipo_incidente_predicho_id bigint,
    nivel_prioridad_predicho varchar(20),
    especialidad_sugerida_id bigint,
    danio_visible_detectado text,
    requiere_remolque_predicho boolean,
    puntaje_confianza numeric(5,2),
    respuesta_cruda_json text,
    fecha_creacion timestamp not null default now(),
    fecha_actualizacion timestamp not null default now(),

    constraint uq_analisis_ia_incidente unique (incidente_id),
    constraint fk_analisis_ia_incidente
        foreign key (incidente_id)
        references incidentes(id)
        on update cascade
        on delete cascade,
    constraint fk_analisis_ia_tipo_predicho
        foreign key (tipo_incidente_predicho_id)
        references tipos_incidente(id)
        on update cascade
        on delete set null,
    constraint fk_analisis_ia_especialidad
        foreign key (especialidad_sugerida_id)
        references especialidades(id)
        on update cascade
        on delete set null,
    constraint chk_analisis_ia_prioridad
        check (
            nivel_prioridad_predicho is null
            or nivel_prioridad_predicho in ('BAJA', 'MEDIA', 'ALTA', 'CRITICA', 'INCIERTA')
        ),
    constraint chk_analisis_ia_confianza
        check (puntaje_confianza is null or puntaje_confianza between 0 and 100)
);

create table if not exists historial_estados_incidente (
    id bigint generated always as identity primary key,
    incidente_id bigint not null,
    estado_incidente_id bigint not null,
    usuario_id bigint,
    observacion varchar(255),
    fecha_cambio timestamp not null default now(),

    constraint fk_historial_incidente
        foreign key (incidente_id)
        references incidentes(id)
        on update cascade
        on delete cascade,
    constraint fk_historial_estado
        foreign key (estado_incidente_id)
        references estados_incidente(id)
        on update cascade
        on delete restrict,
    constraint fk_historial_usuario
        foreign key (usuario_id)
        references usuarios(id)
        on update cascade
        on delete set null
);

create table if not exists candidatos_taller_incidente (
    id bigint generated always as identity primary key,
    incidente_id bigint not null,
    taller_id bigint not null,
    puntaje numeric(10,2),
    distancia_km numeric(10,2),
    tiempo_estimado_llegada_min integer,
    fue_notificado boolean not null default false,
    fecha_notificacion timestamp,
    estado_respuesta varchar(30) not null default 'PENDIENTE',
    fecha_respuesta timestamp,
    observacion_respuesta varchar(255),

    constraint uq_candidato_taller_incidente unique (incidente_id, taller_id),
    constraint fk_candidatos_incidente
        foreign key (incidente_id)
        references incidentes(id)
        on update cascade
        on delete cascade,
    constraint fk_candidatos_taller
        foreign key (taller_id)
        references talleres(id)
        on update cascade
        on delete restrict,
    constraint chk_candidatos_puntaje
        check (puntaje is null or puntaje >= 0),
    constraint chk_candidatos_distancia
        check (distancia_km is null or distancia_km >= 0),
    constraint chk_candidatos_tiempo
        check (tiempo_estimado_llegada_min is null or tiempo_estimado_llegada_min >= 0),
    constraint chk_candidatos_estado_respuesta
        check (estado_respuesta in ('PENDIENTE', 'ACEPTADO', 'RECHAZADO', 'EXPIRADO'))
);

create table if not exists asignaciones_servicio (
    id bigint generated always as identity primary key,
    incidente_id bigint not null,
    taller_id bigint not null,
    tecnico_id bigint,
    especialidad_id bigint,
    usuario_asignador_id bigint,
    descripcion_servicio_realizado text,
    distancia_km numeric(10,2),
    tiempo_estimado_llegada_min integer,
    costo_estimado numeric(10,2),
    costo_final numeric(10,2),
    estado_asignacion varchar(30) not null default 'ASIGNADO',
    observaciones_finales text,
    fecha_asignacion timestamp not null default now(),
    fecha_creacion timestamp not null default now(),
    fecha_actualizacion timestamp not null default now(),

    constraint uq_asignaciones_incidente unique (incidente_id),
    constraint fk_asignaciones_incidente
        foreign key (incidente_id)
        references incidentes(id)
        on update cascade
        on delete cascade,
    constraint fk_asignaciones_taller
        foreign key (taller_id)
        references talleres(id)
        on update cascade
        on delete restrict,
    constraint fk_asignaciones_tecnico
        foreign key (tecnico_id)
        references tecnicos(id)
        on update cascade
        on delete set null,
    constraint fk_asignaciones_especialidad
        foreign key (especialidad_id)
        references especialidades(id)
        on update cascade
        on delete set null,
    constraint fk_asignaciones_usuario_asignador
        foreign key (usuario_asignador_id)
        references usuarios(id)
        on update cascade
        on delete set null,
    constraint chk_asignaciones_distancia
        check (distancia_km is null or distancia_km >= 0),
    constraint chk_asignaciones_tiempo
        check (tiempo_estimado_llegada_min is null or tiempo_estimado_llegada_min >= 0),
    constraint chk_asignaciones_costo_estimado
        check (costo_estimado is null or costo_estimado >= 0),
    constraint chk_asignaciones_costo_final
        check (costo_final is null or costo_final >= 0),
    constraint chk_asignaciones_estado
        check (
            estado_asignacion in (
                'ASIGNADO',
                'EN_CAMINO',
                'EN_PROCESO',
                'ATENDIDO',
                'CANCELADO',
                'PENDIENTE_PAGO',
                'PAGADO'
            )
        )
);

create table if not exists pagos (
    id bigint generated always as identity primary key,
    asignacion_servicio_id bigint not null,
    cliente_usuario_id bigint not null,
    monto numeric(10,2) not null,
    moneda varchar(10) not null default 'BOB',
    metodo_pago varchar(30) not null,
    proveedor_pago varchar(50),
    referencia_externa varchar(150),
    estado_pago varchar(30) not null default 'PENDIENTE',
    fecha_pago timestamp,
    fecha_creacion timestamp not null default now(),

    constraint uq_pagos_asignacion unique (asignacion_servicio_id),
    constraint fk_pagos_asignacion
        foreign key (asignacion_servicio_id)
        references asignaciones_servicio(id)
        on update cascade
        on delete cascade,
    constraint fk_pagos_cliente
        foreign key (cliente_usuario_id)
        references usuarios(id)
        on update cascade
        on delete restrict,
    constraint chk_pagos_monto
        check (monto >= 0),
    constraint chk_pagos_metodo
        check (metodo_pago in ('QR', 'EFECTIVO', 'TRANSFERENCIA')),
    constraint chk_pagos_estado
        check (estado_pago in ('PENDIENTE', 'PAGADO', 'FALLIDO', 'CANCELADO'))
);

create table if not exists calificaciones (
    id bigint generated always as identity primary key,
    asignacion_servicio_id bigint not null,
    cliente_usuario_id bigint not null,
    puntuacion integer not null,
    comentario varchar(255),
    fecha_creacion timestamp not null default now(),

    constraint uq_calificaciones_asignacion unique (asignacion_servicio_id),
    constraint fk_calificaciones_asignacion
        foreign key (asignacion_servicio_id)
        references asignaciones_servicio(id)
        on update cascade
        on delete cascade,
    constraint fk_calificaciones_cliente
        foreign key (cliente_usuario_id)
        references usuarios(id)
        on update cascade
        on delete restrict,
    constraint chk_calificaciones_puntuacion
        check (puntuacion between 1 and 5)
);

create table if not exists notificaciones (
    id bigint generated always as identity primary key,
    usuario_id bigint,
    incidente_id bigint,
    tipo_notificacion varchar(50) not null,
    canal varchar(30) not null,
    titulo varchar(150) not null,
    mensaje varchar(255) not null,
    datos_adicionales_json text,
    estado varchar(30) not null default 'PENDIENTE',
    fecha_envio timestamp,
    fecha_lectura timestamp,
    fecha_creacion timestamp not null default now(),

    constraint fk_notificaciones_usuario
        foreign key (usuario_id)
        references usuarios(id)
        on update cascade
        on delete set null,
    constraint fk_notificaciones_incidente
        foreign key (incidente_id)
        references incidentes(id)
        on update cascade
        on delete set null,
    constraint chk_notificaciones_canal
        check (canal in ('PUSH', 'EMAIL', 'SMS', 'IN_APP')),
    constraint chk_notificaciones_estado
        check (estado in ('PENDIENTE', 'ENVIADA', 'LEIDA', 'FALLIDA'))
);

-- =========================================================
-- INDICES
-- =========================================================

create index if not exists idx_vehiculos_usuario_id
    on vehiculos(usuario_id);

create index if not exists idx_horarios_taller_taller_id
    on horarios_taller(taller_id);

create index if not exists idx_taller_especialidades_taller_id
    on taller_especialidades(taller_id);

create index if not exists idx_taller_especialidades_especialidad_id
    on taller_especialidades(especialidad_id);

create index if not exists idx_tecnicos_taller_id
    on tecnicos(taller_id);

create index if not exists idx_tecnicos_estado_disponibilidad
    on tecnicos(estado_disponibilidad);

create index if not exists idx_tecnico_especialidades_tecnico_id
    on tecnico_especialidades(tecnico_id);

create index if not exists idx_tecnico_especialidades_especialidad_id
    on tecnico_especialidades(especialidad_id);

create index if not exists idx_incidentes_cliente_usuario_id
    on incidentes(cliente_usuario_id);

create index if not exists idx_incidentes_vehiculo_id
    on incidentes(vehiculo_id);

create index if not exists idx_incidentes_tipo_incidente_id
    on incidentes(tipo_incidente_id);

create index if not exists idx_incidentes_estado_incidente_id
    on incidentes(estado_incidente_id);

create index if not exists idx_incidentes_fecha_solicitud
    on incidentes(fecha_solicitud);

create index if not exists idx_evidencias_incidente_id
    on evidencias_incidente(incidente_id);

create index if not exists idx_historial_incidente_id
    on historial_estados_incidente(incidente_id);

create index if not exists idx_historial_estado_id
    on historial_estados_incidente(estado_incidente_id);

create index if not exists idx_candidatos_incidente_id
    on candidatos_taller_incidente(incidente_id);

create index if not exists idx_candidatos_taller_id
    on candidatos_taller_incidente(taller_id);

create index if not exists idx_asignaciones_taller_id
    on asignaciones_servicio(taller_id);

create index if not exists idx_asignaciones_tecnico_id
    on asignaciones_servicio(tecnico_id);

create index if not exists idx_asignaciones_especialidad_id
    on asignaciones_servicio(especialidad_id);

create index if not exists idx_asignaciones_estado
    on asignaciones_servicio(estado_asignacion);

create index if not exists idx_pagos_cliente_usuario_id
    on pagos(cliente_usuario_id);

create index if not exists idx_pagos_estado_pago
    on pagos(estado_pago);

create index if not exists idx_calificaciones_cliente_usuario_id
    on calificaciones(cliente_usuario_id);

create index if not exists idx_notificaciones_usuario_id
    on notificaciones(usuario_id);

create index if not exists idx_notificaciones_incidente_id
    on notificaciones(incidente_id);

create index if not exists idx_notificaciones_estado
    on notificaciones(estado);

-- =========================================================
-- TRIGGERS fecha_actualizacion
-- =========================================================

drop trigger if exists trg_usuarios_fecha_actualizacion on usuarios;
create trigger trg_usuarios_fecha_actualizacion
before update on usuarios
for each row
execute function actualizar_fecha_actualizacion();

drop trigger if exists trg_talleres_fecha_actualizacion on talleres;
create trigger trg_talleres_fecha_actualizacion
before update on talleres
for each row
execute function actualizar_fecha_actualizacion();

drop trigger if exists trg_vehiculos_fecha_actualizacion on vehiculos;
create trigger trg_vehiculos_fecha_actualizacion
before update on vehiculos
for each row
execute function actualizar_fecha_actualizacion();

drop trigger if exists trg_especialidades_fecha_actualizacion on especialidades;
create trigger trg_especialidades_fecha_actualizacion
before update on especialidades
for each row
execute function actualizar_fecha_actualizacion();

drop trigger if exists trg_tecnicos_fecha_actualizacion on tecnicos;
create trigger trg_tecnicos_fecha_actualizacion
before update on tecnicos
for each row
execute function actualizar_fecha_actualizacion();

drop trigger if exists trg_tipos_incidente_fecha_actualizacion on tipos_incidente;
create trigger trg_tipos_incidente_fecha_actualizacion
before update on tipos_incidente
for each row
execute function actualizar_fecha_actualizacion();

drop trigger if exists trg_estados_incidente_fecha_actualizacion on estados_incidente;
create trigger trg_estados_incidente_fecha_actualizacion
before update on estados_incidente
for each row
execute function actualizar_fecha_actualizacion();

drop trigger if exists trg_incidentes_fecha_actualizacion on incidentes;
create trigger trg_incidentes_fecha_actualizacion
before update on incidentes
for each row
execute function actualizar_fecha_actualizacion();

drop trigger if exists trg_analisis_ia_incidente_fecha_actualizacion on analisis_ia_incidente;
create trigger trg_analisis_ia_incidente_fecha_actualizacion
before update on analisis_ia_incidente
for each row
execute function actualizar_fecha_actualizacion();

drop trigger if exists trg_asignaciones_servicio_fecha_actualizacion on asignaciones_servicio;
create trigger trg_asignaciones_servicio_fecha_actualizacion
before update on asignaciones_servicio
for each row
execute function actualizar_fecha_actualizacion();

-- =========================================================
-- DATOS BASE
-- =========================================================

insert into tipos_incidente (nombre, descripcion)
values
    ('BATERIA', 'Problemas relacionados con bateria o sistema electrico basico'),
    ('LLANTA', 'Pinchazo, reventon o problema de llantas'),
    ('CHOQUE', 'Accidente o colision leve'),
    ('MOTOR', 'Problema mecanico de motor'),
    ('LLAVE', 'Llave perdida, olvidada o problema de apertura'),
    ('INCIERTO', 'Caso ambiguo o no clasificado')
on conflict (nombre) do nothing;

insert into estados_incidente (nombre, descripcion, orden)
values
    ('PENDIENTE', 'Incidente reportado y pendiente de procesamiento', 1),
    ('NOTIFICADO', 'Talleres candidatos ya fueron notificados', 2),
    ('ACEPTADO', 'Un taller acepto la solicitud', 3),
    ('EN_PROCESO', 'La atencion del servicio esta en curso', 4),
    ('ATENDIDO', 'El incidente fue atendido', 5),
    ('CANCELADO', 'El incidente fue cancelado', 6),
    ('PENDIENTE_PAGO', 'El servicio fue atendido y espera pago', 7),
    ('PAGADO', 'El pago fue confirmado', 8)
on conflict (nombre) do nothing;

insert into especialidades (nombre, descripcion)
values
    ('BATERIA', 'Atencion de problemas de bateria y sistema electrico'),
    ('LLANTAS', 'Atencion de pinchazos, cambio o reparacion de llantas'),
    ('MOTOR', 'Atencion de fallas de motor'),
    ('SUSPENSION', 'Atencion de problemas de suspension'),
    ('CERRAJERIA_VEHICULAR', 'Apertura o asistencia por llaves'),
    ('REMOLQUE', 'Traslado del vehiculo mediante remolque')
on conflict (nombre) do nothing;