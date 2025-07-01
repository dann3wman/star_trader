from contextlib import contextmanager
from sqlalchemy import create_engine, Column, String, Integer, Float
from sqlalchemy.orm import sessionmaker, declarative_base

# Database path is configured via the shared config module
from config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


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


class GoodsTable(Base):
    __tablename__ = "goods"
    name = Column(String, primary_key=True)
    size = Column(Float)


class JobsTable(Base):
    __tablename__ = "jobs"
    name = Column(String, primary_key=True)
    job_limit = Column(Integer)


class JobInput(Base):
    __tablename__ = "job_inputs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job = Column(String)
    good = Column(String)
    qty = Column(Integer)


class JobOutput(Base):
    __tablename__ = "job_outputs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job = Column(String)
    good = Column(String)
    qty = Column(Integer)


class JobTool(Base):
    __tablename__ = "job_tools"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job = Column(String)
    tool = Column(String)
    qty = Column(Integer)
    break_chance = Column(Float)


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

