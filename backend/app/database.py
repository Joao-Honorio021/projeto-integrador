from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .core.config import DATABASE_URL, BACKEND_DIR
url = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
options = {'connect_args': {'check_same_thread': False}} if url.startswith('sqlite:') else {'pool_size': 3, 'max_overflow': 2, 'pool_recycle': 300}
engine = create_engine(url, pool_pre_ping=True, hide_parameters=True, **options)
if engine.dialect.name == 'sqlite':
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
    """Aplique migrações explicitamente em produção; desenvolvimento mantém startup compatível."""
    from alembic.config import Config
    from alembic import command
    config = Config(str(BACKEND_DIR / 'alembic.ini'))
    config.set_main_option('script_location', str(BACKEND_DIR / 'migrations'))
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        command.upgrade(config, 'head')
