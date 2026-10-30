from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .core.config import DATABASE_URL, BACKEND_DIR
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

@event.listens_for(engine, 'connect')
def foreign_keys(connection, _):
    connection.execute('PRAGMA foreign_keys=ON')

class Base(DeclarativeBase):
    pass
Session = sessionmaker(engine)

def db_session():
    with Session() as db:
        try:
            yield db
        except Exception:
            db.rollback()
            raise

def initialize_database():
    """DDL SQL versionado, compatível com bancos da primeira etapa."""
    script = (BACKEND_DIR / 'sql' / 'schema.sql').read_text()
    with engine.begin() as connection:
        for statement in script.split(';'):
            if statement.strip():
                connection.exec_driver_sql(statement)
