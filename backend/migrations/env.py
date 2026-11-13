from alembic import context
from app.database import engine

def migrate(connection):
    context.configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()
connection = context.config.attributes.get('connection')
if connection is not None:
    migrate(connection)
else:
    with engine.connect() as connection:
        migrate(connection)
