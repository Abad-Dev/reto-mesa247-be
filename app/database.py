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


def init_db() -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        _run_sql_file(connection, "schema.sql")
        _ensure_columns(connection)

        locales = connection.execute("SELECT COUNT(*) FROM local").fetchone()[0]
        if locales == 0:
            _run_sql_file(connection, "seed.sql")

        connection.commit()

    return DB_PATH


if __name__ == "__main__":
    db_file = init_db()
    print(f"SQLite listo en {db_file}")
