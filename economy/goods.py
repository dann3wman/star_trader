from dataclasses import dataclass
from typing import Dict, Iterator, List

from sqlalchemy import select

from . import db
from .utils import seed_if_empty



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
    with db.session_scope() as session:
        rows = seed_if_empty(
            session,
            select(db.GoodsTable.name, db.GoodsTable.size),
            "goods.yml",
            lambda s, data: s.add_all(
                [db.GoodsTable(name=g["name"], size=g["size"]) for g in data]
            ),
        )

        for name, size in rows:
            Good(name=name, size=size)


_load_goods()
