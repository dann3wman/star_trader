import os
from dataclasses import dataclass
from typing import Dict, Iterator, List

import yaml
from sqlalchemy import select

from . import db



_by_name: Dict[str, "Good"] = {}

def by_name(name: str) -> "Good":
    return _by_name[name.lower()]

_goods: List["Good"] = []

def all() -> Iterator["Good"]:
    for good in _goods:
        yield good


@dataclass(slots=True, frozen=True)
class Good:
    name: str
    size: float

    def __post_init__(self) -> None:
        _by_name[self.name.lower()] = self
        _goods.append(self)

    def __str__(self):
        return self.name



def _load_goods():
    """Load goods from the database, populating tables from YAML if needed."""
    db.Base.metadata.create_all(bind=db.engine, tables=[db.GoodsTable.__table__])
    session = db.get_session()
    rows = session.execute(select(db.GoodsTable.name, db.GoodsTable.size)).all()
    if not rows:
        with open(os.path.join("data", "goods.yml")) as fh:
            data = yaml.safe_load(fh)
        objs = [db.GoodsTable(name=g["name"], size=g["size"]) for g in data]
        session.add_all(objs)
        session.commit()
        rows = [(g["name"], g["size"]) for g in data]

    for name, size in rows:
        Good(name=name, size=size)
    session.close()


_load_goods()

