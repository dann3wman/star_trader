from collections import namedtuple
import os
import yaml

from . import db



_by_name = {}

def by_name(name):
    return _by_name[name.lower()]

_goods = []
def all():
    for good in _goods:
        yield good


class Good(namedtuple('Good', ['name','size'])):
    __slots__ = ()
    def __init__(self, *args, **kwargs):
        _by_name[self.name.lower()] = self
        _goods.append(self)

    def __str__(self):
        return self.name



def _load_goods():
    """Load goods from the database, populating tables from YAML if needed."""
    conn = db.get_connection()
    with conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS goods(
                    name TEXT PRIMARY KEY,
                    size REAL
                )"""
        )
        cur = conn.execute("SELECT name, size FROM goods")
        rows = cur.fetchall()
        if not rows:
            with open(os.path.join("data", "goods.yml")) as fh:
                data = yaml.safe_load(fh)
            conn.executemany(
                "INSERT INTO goods(name, size) VALUES (?, ?)",
                [(g["name"], g["size"]) for g in data],
            )
            rows = [(g["name"], g["size"]) for g in data]

    for name, size in rows:
        Good(name=name, size=size)


_load_goods()

