try:
    from .market import Market
except Exception:
    # Import errors here are likely due to optional dependencies used by
    # the market implementation (e.g. PyYAML when loading goods). To allow
    # package import without these extras during tests, ignore failures.
    Market = None
