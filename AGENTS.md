# Agent instructions

when in doubt, do the next step before prompting

## Required docs

- `docs/REPO_STYLE.md`
- `docs/PYTHON_STYLE.md`
- `docs/PYTEST_STYLE.md`
- `docs/MARKDOWN_STYLE.md`
- `docs/CHANGELOG.md`

## Commands

- Run every Python command with `source source_me.sh && python3` using Python 3.12.
- Python modules are installed under `/opt/homebrew/lib/python3.12/site-packages/`.
- Run the full suite with `source source_me.sh && python3 -m pytest tests/`.

## Git

- Humans handle Git index and history operations; agents leave edits unstaged and uncommitted.
