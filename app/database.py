import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = BASE_DIR / "sql"
DB_PATH = BASE_DIR / "data" / "mesa247.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_sql_file(connection: sqlite3.Connection, filename: str) -> None:
    script = (SQL_DIR / filename).read_text(encoding="utf-8")
    connection.executescript(script)


def _ensure_columns(connection: sqlite3.Connection) -> None:
    columns = {row[1] for row in connection.execute("PRAGMA table_info(entrada_cola)")}
    if "tiempo_estimado_minutos" not in columns:
        connection.execute("ALTER TABLE entrada_cola ADD COLUMN tiempo_estimado_minutos INTEGER")


def _ensure_estado_en_camino(connection: sqlite3.Connection) -> None:
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='entrada_cola'"
    ).fetchone()
    if row is None or "en_camino" in row[0]:
        return

    connection.execute("PRAGMA foreign_keys=OFF")
    connection.executescript(
        """
        CREATE TABLE entrada_cola_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_local INTEGER NOT NULL,
            nombre_comensal TEXT NOT NULL,
            telefono_comensal TEXT NOT NULL,
            cantidad_personas INTEGER NOT NULL CHECK (cantidad_personas > 0),
            estado TEXT NOT NULL DEFAULT 'esperando' CHECK (
                estado IN ('esperando', 'llamado', 'en_camino', 'sentado', 'no_show', 'cancelado')
            ),
            "orden" INTEGER NOT NULL,
            es_frecuente INTEGER NOT NULL DEFAULT 0 CHECK (es_frecuente IN (0, 1)),
            id_mesa INTEGER,
            fecha_hora_union DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            fecha_hora_llamado DATETIME,
            tiempo_estimado_minutos INTEGER CHECK (
                tiempo_estimado_minutos IS NULL OR tiempo_estimado_minutos >= 0
            ),
            FOREIGN KEY (id_local) REFERENCES local(id) ON DELETE RESTRICT,
            FOREIGN KEY (id_mesa) REFERENCES mesa(id) ON DELETE SET NULL
        );

        INSERT INTO entrada_cola_new (
            id, id_local, nombre_comensal, telefono_comensal, cantidad_personas,
            estado, "orden", es_frecuente, id_mesa, fecha_hora_union,
            fecha_hora_llamado, tiempo_estimado_minutos
        )
        SELECT
            id, id_local, nombre_comensal, telefono_comensal, cantidad_personas,
            estado, "orden", es_frecuente, id_mesa, fecha_hora_union,
            fecha_hora_llamado, tiempo_estimado_minutos
        FROM entrada_cola;

        DROP TABLE entrada_cola;
        ALTER TABLE entrada_cola_new RENAME TO entrada_cola;

        CREATE INDEX IF NOT EXISTS ix_entrada_cola_local_estado_orden
            ON entrada_cola (id_local, estado, "orden");
        """
    )
    connection.execute("PRAGMA foreign_keys=ON")


def init_db() -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        _run_sql_file(connection, "schema.sql")
        _ensure_columns(connection)
        _ensure_estado_en_camino(connection)

        locales = connection.execute("SELECT COUNT(*) FROM local").fetchone()[0]
        if locales == 0:
            _run_sql_file(connection, "seed.sql")

        connection.commit()

    return DB_PATH


if __name__ == "__main__":
    db_file = init_db()
    print(f"SQLite listo en {db_file}")
