# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-11-03

### Added

- **Storage Abstraction Layer**: Introduced a flexible storage system with a `BaseStorage` abstract base class.
- **JSON and SQLite Storage**: Implemented `JsonStorage` (default) and `SqliteStorage` for persisting agent execution
  traces.
- **CLI Trace Explorer**: Added a new `agenthelm traces` command group to the CLI.
- **`traces list` command**: List recent traces with pagination and JSON output option.
- **`traces show` command**: Show detailed information for a specific trace.
- **`traces filter` command**: Filter traces by various criteria like tool name, status, date, execution time, and
  confidence score.
- **`traces export` command**: Export filtered traces to JSON, CSV, or Markdown formats.
- **Observability Documentation**: Added `docs/observability.md` with detailed information on the new features.
- **Observability Example**: Added a new example in `examples/observability_example/` to demonstrate the new storage and
  CLI features.

### Changed

- **Standardized Logging**: Replaced all `print()` statements with Python's standard `logging` module for better control
  over output verbosity.
- **CLI Entry Point**: The main CLI entry point is now `orchestrator.cli:app`.
- **Dependencies**: Added `tabulate` as a new dependency for table formatting in the CLI.
- **Project Structure**: Moved storage-related classes to the `orchestrator/core/storage/` directory.

### Fixed

- Corrected various import errors and fixed linter warnings identified by `ruff`.
- Fixed an issue where the SQLite database file was being deleted after table creation in the example agent.
- Resolved issues with CLI test failures by using `typer.echo` for output and fixing indentation errors.
