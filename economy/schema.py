from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


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
