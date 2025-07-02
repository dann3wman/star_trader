from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database path is configured via the shared config module
from config import DB_PATH

from .schema import (
    Base,
    GoodsTable,
    JobsTable,
    JobInput,
    JobOutput,
    JobTool,
)

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)


def get_session():
    """Return a new SQLAlchemy session bound to the shared engine."""
    return SessionLocal()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def rebuild_database():
    """Recreate goods and jobs tables from YAML files."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Clear any cached data and reload from YAML
    from . import goods as goods_mod, jobs as jobs_mod

    goods_mod._goods.clear()
    goods_mod._by_name.clear()
    jobs_mod._jobs.clear()
    jobs_mod._by_name.clear()

    goods_mod._load_goods()
    jobs_mod._load_jobs()
