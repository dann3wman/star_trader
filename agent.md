# Development Guidelines

- Format all Python code using [Black](https://black.readthedocs.io/). Run `black` on any modified `*.py` files before committing changes.
- After formatting, execute `pytest` to ensure the unit tests still pass.
- Add new dependencies to `requirements.txt`.
- Keep documentation up to date. Update the README and add docstrings or comments when refactoring or introducing new features.
- When you complete an item from `REFACTORING.md`, cross it off using Markdown strikethrough, move the crossed-out task to the bottom of the file, and append at least one new refactoring opportunity to the end of the list. This keeps the document current and encourages continued improvements.
