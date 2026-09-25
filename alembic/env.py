"""Alembic env — autogenerate from app.database.models.Base."""
from alembic import context
from sqlalchemy import create_engine
from app.database.models import Base
from app.config.settings import settings

config = context.config
url = settings.db_url
engine = create_engine(url)

with engine.connect() as conn:
    context.configure(connection=conn, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
