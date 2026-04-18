# Contributing

Contributions are welcome via pull requests at [github.com/raetha/ha-scrutiny](https://github.com/raetha/ha-scrutiny).

## Development setup

1. Clone the repository
2. Install test dependencies: `pip install -r requirements.txt`
3. Run the test suite: `pytest tests/ -v`
4. Run the linter: `ruff check custom_components/scrutiny/`

## Before submitting a PR

- All tests pass (`pytest tests/`)
- Ruff reports no issues (`ruff check custom_components/scrutiny/`)
- Ruff formatting is clean (`ruff format --check custom_components/scrutiny/`)
- If adding a new feature, update `CHANGELOG.md` under an `Unreleased` section
