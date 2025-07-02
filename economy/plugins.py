import importlib
import pkgutil
from typing import Dict, Type

from economy.agent import Agent

_loaded = False
_agent_classes: Dict[str, Type[Agent]] = {}
_job_agents: Dict[str, Type[Agent]] = {}


def register_agent(cls: Type[Agent], job: str | None = None) -> None:
    """Register a custom Agent subclass.

    Parameters
    ----------
    cls : Type[Agent]
        The Agent subclass to register.
    job : str, optional
        Name of the job this agent should handle. If provided the market
        will use this class when spawning agents for that job.
    """
    name = cls.__name__
    _agent_classes[name] = cls
    if job:
        _job_agents[job.lower()] = cls


def agent_for_job(job: str) -> Type[Agent]:
    """Return the Agent class registered for ``job`` if any."""
    return _job_agents.get(job.lower(), Agent)


def load_plugins() -> None:
    """Import all modules in the top-level ``plugins`` package."""
    global _loaded
    if _loaded:
        return
    try:
        import plugins  # type: ignore
    except Exception:
        _loaded = True
        return
    for finder, name, ispkg in pkgutil.iter_modules(plugins.__path__):
        module = importlib.import_module(f"plugins.{name}")
        if hasattr(module, "register"):
            module.register()
    _loaded = True
