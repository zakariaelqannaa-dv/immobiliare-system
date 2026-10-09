"""Alembic env — autogenerate from app.database.models.Base."""
from __future__ import annotations

import os
from alembic import context
from sqlalchemy import create_engine, event
from app.database.models import Base

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

config = context.config
url = os.getenv("IMMOBILIARE_DB_URL") or config.get_main_option("sqlalchemy.url")

engine = create_engine(url)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_conn, _rec):
    try:
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
    except Exception:
        pass


def run_migrations_online():
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=Base.metadata,
                          compare_type=True, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
