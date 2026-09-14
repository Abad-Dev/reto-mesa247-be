PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS local (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mesa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_local INTEGER NOT NULL,
    capacidad INTEGER NOT NULL CHECK (capacidad > 0),
    FOREIGN KEY (id_local) REFERENCES local(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS entrada_cola (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_local INTEGER NOT NULL,
    nombre_comensal TEXT NOT NULL,
    telefono_comensal TEXT NOT NULL,
    cantidad_personas INTEGER NOT NULL CHECK (cantidad_personas > 0),
    estado TEXT NOT NULL DEFAULT 'esperando' CHECK (
        estado IN ('esperando', 'llamado', 'sentado', 'no_show', 'cancelado')
    ),
    "orden" INTEGER NOT NULL,
    es_frecuente INTEGER NOT NULL DEFAULT 0 CHECK (es_frecuente IN (0, 1)),
    id_mesa INTEGER,
    fecha_hora_union DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    fecha_hora_llamado DATETIME,
    FOREIGN KEY (id_local) REFERENCES local(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_mesa) REFERENCES mesa(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_mesa_id_local ON mesa (id_local);
CREATE INDEX IF NOT EXISTS ix_entrada_cola_local_estado_orden
    ON entrada_cola (id_local, estado, "orden");
