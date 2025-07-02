# Refactoring Opportunities

The following areas could benefit from a refactor to improve maintainability and clarity of the Star Trader codebase.

## 1. Split large modules
- `economy/agent.py` contains the `Agent` class, the `Inventory` class and very long constant lists of names. Separating these concerns into multiple modules would keep each file focused and easier to navigate.
- Moving `Inventory` to its own file would also allow dedicated unit tests and reuse without importing all agent logic.

## 2. Reduce inline data
- The lists of `FIRST_NAMES` and `LAST_NAMES` in `agent.py` are hundreds of lines long. Storing them in data files (JSON/YAML) or generating names via a library would shrink the codebase and make updates simpler.

## 3. Adopt dataclasses and typing
- Many classes such as `Good`, `JobStep` and `JobTool` mainly store data. Converting them to `dataclass`es with type hints would make their intent clearer and reduce boilerplate.
- Adding type hints across the project would help tooling catch bugs earlier and improve readability.

## 4. Replace `print` with logging
- Debug information and order matching output are written using `print`. Using the `logging` module would give better control over log levels and destinations.

## 5. Clean database interactions
- Functions in `economy/db.py` manually open and close SQLAlchemy sessions. Using context managers or a dependency injection approach would ensure sessions are closed even if errors occur.

## 6. Simplify job and goods loading
- The `_load_goods` and `_load_jobs` functions perform similar steps for seeding the database from YAML. Extracting common logic or using an ORM abstraction layer could reduce duplication.

## 7. Improved configuration management
- Configuration like `DB_PATH`, inventory size, and initial money are scattered across modules. Centralizing configuration (for example via environment variables or a configuration file) would make it easier to modify these values and test different scenarios.

## 8. Break up monolithic functions
- Some functions, such as `Market.simulate`, contain many nested loops and side effects. Breaking them into smaller helper methods would aid comprehension and testing.

## 9. Modularize CLI and GUI
- The command-line tool in `simulate.py` and the web interface in `gui/app.py` both create and manage `Market` instances. A shared controller module would remove duplication and keep behaviour consistent across interfaces.

## 10. Lazy load name lists
- `economy/names.py` reads `names.yml` at import time. Loading this data only when names are requested would speed up startup and make it easier to supply alternative name lists.

## 11. Introduce custom exceptions
- Many error cases raise generic exceptions. Defining domain-specific exception classes would clarify intent and allow callers to handle failures more precisely.

## 12. Consolidate database schema
- Table definitions in `economy/db.py` sit alongside session helpers. Moving the schema into a dedicated module would separate concerns and simplify future migrations.

## 13. Use dataclasses for market orders
- `Bid` and `Ask` in `offer.py` manage attributes manually. Converting them to dataclasses would reduce boilerplate and provide built-in representations.

## 14. Replace `namedtuple` in history with a dataclass
- The `Trades` tuple in `market/history.py` lacks defaults and type hints. A dataclass would be easier to extend and document.

## 15. Use context managers for file operations
- Some modules open files without `with` statements. Employing context managers ensures files are closed properly even when errors occur.

## 16. Extract repeated YAML parsing logic
- Loading YAML data is repeated in several places (`goods.py`, `jobs.py`, `names.py`). A helper function would reduce duplication and centralize error handling.

## 17. Improve path handling
- Paths are built using string concatenation or `os.path.join`. Adopting `pathlib.Path` would improve readability and cross-platform support.

## 18. Encapsulate simulation state
- `Market` exposes a number of mutable attributes directly. Restricting access through methods or properties would help maintain invariants and enable future concurrency features.

These changes are not required for functionality, but they would make the project easier to maintain and extend.
