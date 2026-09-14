from app.database import init_db

if __name__ == "__main__":
    db_file = init_db()
    print(f"SQLite listo en {db_file}")
