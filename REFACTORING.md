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

These changes are not required for functionality, but they would make the project easier to maintain and extend.
