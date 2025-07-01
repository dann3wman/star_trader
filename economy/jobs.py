import os
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

import yaml
from sqlalchemy import select

from . import db


from . import goods


_by_name: Dict[str, "Job"] = {}

def by_name(name: str) -> "Job":
    return _by_name[name.lower()]

_jobs: List["Job"] = []

def all() -> Iterator["Job"]:
    for job in _jobs:
        yield job


@dataclass(slots=True)
class JobStep:
    good: goods.Good
    qty: int


@dataclass(slots=True)
class JobTool:
    tool: goods.Good
    qty: int
    break_chance: float


class Job(object):
    __slots__ = ("__inputs", "__outputs", "__tools", "__name", "__limit")

    def __init__(
        self,
        name: str,
        inputs: Optional[Iterable[Dict[str, object]]] = None,
        outputs: Optional[Iterable[Dict[str, object]]] = None,
        tools: Optional[Iterable[Dict[str, object]]] = None,
        limit: Optional[int] = None,
    ) -> None:
        self.__name = name
        self.__limit = limit

        inputs = inputs or []
        outputs = outputs or []
        tools = tools or []

        self.__inputs = ()
        for step in inputs:
            step['good'] = goods.by_name(step['good'])
            self.__inputs += (JobStep(**step),)

        self.__outputs = ()
        for step in outputs:
            step['good'] = goods.by_name(step['good'])
            self.__outputs += (JobStep(**step),)

        self.__tools = ()
        for tool in tools:
            tool['tool'] = goods.by_name(tool['tool'])
            self.__tools += (JobTool(**tool),)

        _by_name[name.lower()] = self
        _jobs.append(self)

    @property
    def inputs(self) -> Tuple[JobStep, ...]:
        return self.__inputs

    @property
    def outputs(self) -> Tuple[JobStep, ...]:
        return self.__outputs

    @property
    def tools(self) -> Tuple[JobTool, ...]:
        return self.__tools

    @property
    def limit(self) -> Optional[int]:
        return self.__limit

    @property
    def runs(self) -> Iterator[bool]:
        if self.limit is None:
            while True:
                yield True
        else:
            for x in range(self.limit):
                yield True

    def __str__(self):
        return self.__name



def _load_jobs() -> None:
    """Load job definitions from the database, using YAML as a seed if empty."""
    db.Base.metadata.create_all(
        bind=db.engine,
        tables=[
            db.JobsTable.__table__,
            db.JobInput.__table__,
            db.JobOutput.__table__,
            db.JobTool.__table__,
        ],
    )

    session = db.get_session()
    rows = session.execute(select(db.JobsTable.name, db.JobsTable.job_limit)).all()
    if not rows:
        with open(os.path.join("data", "jobs.yml")) as fh:
            data = yaml.safe_load(fh)
        for job in data:
            session.add(db.JobsTable(name=job["name"], job_limit=job.get("limit")))
            for step in job.get("inputs", []):
                session.add(db.JobInput(job=job["name"], good=step["good"], qty=step["qty"]))
            for step in job.get("outputs", []):
                session.add(db.JobOutput(job=job["name"], good=step["good"], qty=step["qty"]))
            for tool in job.get("tools", []):
                session.add(
                    db.JobTool(
                        job=job["name"],
                        tool=tool["tool"],
                        qty=tool["qty"],
                        break_chance=tool["break_chance"],
                    )
                )
        session.commit()
        rows = session.execute(select(db.JobsTable.name, db.JobsTable.job_limit)).all()

    for name, job_limit in rows:
        inputs = [
            {"good": r.good, "qty": r.qty}
            for r in session.query(db.JobInput).filter_by(job=name).all()
        ]
        outputs = [
            {"good": r.good, "qty": r.qty}
            for r in session.query(db.JobOutput).filter_by(job=name).all()
        ]
        tools = [
            {"tool": r.tool, "qty": r.qty, "break_chance": r.break_chance}
            for r in session.query(db.JobTool).filter_by(job=name).all()
        ]
        Job(name=name, inputs=inputs, outputs=outputs, tools=tools, limit=job_limit)

    session.close()


_load_jobs()

