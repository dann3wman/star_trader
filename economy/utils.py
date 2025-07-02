import os
import yaml
from typing import Callable, Iterable, Any
from sqlalchemy.orm import Session


def load_yaml_file(filename: str) -> Any:
    """Load a YAML file from the ``data`` directory."""
    with open(os.path.join("data", filename)) as fh:
        return yaml.safe_load(fh)


def seed_if_empty(
    session: Session,
    query,
    yaml_file: str,
    loader: Callable[[Session, Iterable[Any]], None],
):
    """Ensure a table has data by seeding from YAML if query returns no rows."""
    rows = session.execute(query).all()
    if not rows:
        data = load_yaml_file(yaml_file)
        loader(session, data)
        session.commit()
        rows = session.execute(query).all()
    return rows
