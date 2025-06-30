from collections import namedtuple
import os
import yaml

from . import db


from . import goods


_by_name = {}
def by_name(name):
    return _by_name[name.lower()]

_jobs = []
def all():
    for job in _jobs:
        yield job


JobStep = namedtuple('JobStep', ['good','qty'])
JobTool = namedtuple('JobTool', ['tool','qty','break_chance'])


class Job(object):
    __slots__ = ('__inputs','__outputs','__tools','__name','__limit')

    def __init__(self, name, inputs=None, outputs=None, tools=None, limit=None):
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
    def inputs(self):
        return self.__inputs

    @property
    def outputs(self):
        return self.__outputs

    @property
    def tools(self):
        return self.__tools

    @property
    def limit(self):
        return self.__limit

    @property
    def runs(self):
        if self.limit is None:
            while True:
                yield True
        else:
            for x in range(self.limit):
                yield True

    def __str__(self):
        return self.__name



def _load_jobs():
    """Load job definitions from the database, using YAML as a seed if empty."""
    conn = db.get_connection()
    with conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS jobs(
                    name TEXT PRIMARY KEY,
                    job_limit INTEGER
                )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS job_inputs(
                    job TEXT,
                    good TEXT,
                    qty INTEGER
                )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS job_outputs(
                    job TEXT,
                    good TEXT,
                    qty INTEGER
                )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS job_tools(
                    job TEXT,
                    tool TEXT,
                    qty INTEGER,
                    break_chance REAL
                )"""
        )

        cur = conn.execute("SELECT name, job_limit FROM jobs")
        rows = cur.fetchall()
        if not rows:
            with open(os.path.join("data", "jobs.yml")) as fh:
                data = yaml.safe_load(fh)
            for job in data:
                conn.execute(
                    "INSERT INTO jobs(name, job_limit) VALUES (?, ?)",
                    (job["name"], job.get("limit")),
                )
                for step in job.get("inputs", []):
                    conn.execute(
                        "INSERT INTO job_inputs(job, good, qty) VALUES (?, ?, ?)",
                        (job["name"], step["good"], step["qty"]),
                    )
                for step in job.get("outputs", []):
                    conn.execute(
                        "INSERT INTO job_outputs(job, good, qty) VALUES (?, ?, ?)",
                        (job["name"], step["good"], step["qty"]),
                    )
                for tool in job.get("tools", []):
                    conn.execute(
                        "INSERT INTO job_tools(job, tool, qty, break_chance) VALUES (?, ?, ?, ?)",
                        (
                            job["name"],
                            tool["tool"],
                            tool["qty"],
                            tool["break_chance"],
                        ),
                    )
            rows = conn.execute("SELECT name, job_limit FROM jobs").fetchall()

    for name, job_limit in rows:
        inputs = [
            {"good": r[0], "qty": r[1]}
            for r in conn.execute(
                "SELECT good, qty FROM job_inputs WHERE job=?", (name,)
            ).fetchall()
        ]
        outputs = [
            {"good": r[0], "qty": r[1]}
            for r in conn.execute(
                "SELECT good, qty FROM job_outputs WHERE job=?", (name,)
            ).fetchall()
        ]
        tools = [
            {"tool": r[0], "qty": r[1], "break_chance": r[2]}
            for r in conn.execute(
                "SELECT tool, qty, break_chance FROM job_tools WHERE job=?",
                (name,),
            ).fetchall()
        ]
        Job(name=name, inputs=inputs, outputs=outputs, tools=tools, limit=job_limit)

    conn.close()


_load_jobs()

