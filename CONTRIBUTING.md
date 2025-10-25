# Contributing to AgentHelm

Thank you for your interest in contributing to AgentHelm! We welcome contributions from the community and are grateful for your support.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and constructive in your interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/hadywalied/agenthelm.git
   cd agenthelm
   ```

## Development Setup

AgentHelm uses `uv` for dependency management. Here's how to set up your development environment:

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python 3.12+** (required):
   ```bash
   uv python install 3.12
   ```

3. **Create a virtual environment and install dependencies**:
   ```bash
   uv sync --all-extras
   ```

4. **Activate the virtual environment**:
   ```bash
   # On Unix/macOS
   source .venv/bin/activate
   
   # On Windows
   .venv\Scripts\activate
   ```

5. **Set up environment variables**:
   ```bash
   # For Mistral AI
   export MISTRAL_API_KEY="your_mistral_api_key_here"
   
   # For OpenAI
   export OPENAI_API_KEY="your_openai_api_key_here"
   ```

## How to Contribute

### Types of Contributions

- **Bug fixes**: Fix issues reported in the issue tracker
- **New features**: Add new functionality or tools
- **Documentation**: Improve docs, add examples, fix typos
- **Tests**: Add test coverage or improve existing tests
- **Performance**: Optimize existing code
- **Refactoring**: Improve code quality and maintainability

### Before You Start

1. **Check existing issues** to see if someone else is already working on it
2. **Open an issue** to discuss your proposed changes (for larger contributions)
3. **Create a branch** from `main` with a descriptive name:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

## Coding Standards

AgentHelm uses **Ruff** for linting and formatting. Please ensure your code adheres to our standards:

1. **Format your code**:
   ```bash
   uv run ruff format .
   ```

2. **Lint your code**:
   ```bash
   uv run ruff check .
   ```

3. **Fix auto-fixable issues**:
   ```bash
   uv run ruff check --fix .
   ```

### Style Guidelines

- Use **type hints** for all function parameters and return values
- Write **descriptive docstrings** for all public functions, classes, and modules
- Follow **PEP 8** conventions
- Keep functions focused and single-purpose
- Use meaningful variable and function names

## Testing

All contributions should include appropriate tests:

1. **Run the test suite**:
   ```bash
   uv run pytest
   ```

2. **Run tests with coverage**:
   ```bash
   uv run pytest --cov=orchestrator --cov-report=html
   ```

3. **Write tests for**:
   - New features
   - Bug fixes
   - Edge cases

### Test Structure

- Place tests in the `tests/` directory
- Mirror the structure of the `orchestrator/` module
- Use descriptive test names: `test_<functionality>_<scenario>_<expected_result>`

## Documentation

Documentation is built with **MkDocs** and **MkDocs Material**:

1. **Serve documentation locally**:
   ```bash
   uv run mkdocs serve
   ```
   View at http://127.0.0.1:8000/

2. **Build documentation**:
   ```bash
   uv run mkdocs build
   ```

### Documentation Guidelines

- Update relevant docs when adding features
- Add examples to demonstrate new functionality
- Keep examples concise and focused
- Update the API reference if needed

## Pull Request Process

1. **Ensure all tests pass** locally before submitting
2. **Update documentation** as needed
3. **Write a clear PR description** that includes:
   - What problem does this solve?
   - What changes were made?
   - How has it been tested?
   - Are there any breaking changes?

4. **Reference related issues** using keywords:
   ```
   Fixes #123
   Closes #456
   ```

5. **Keep PRs focused**: One feature or fix per PR when possible

6. **Respond to feedback**: Be open to suggestions and requested changes

### PR Title Format

Use conventional commit format:
- `feat: Add new feature`
- `fix: Fix bug in tool execution`
- `docs: Update contributing guide`
- `test: Add tests for retry logic`
- `refactor: Improve error handling`
- `perf: Optimize trace logging`

## Reporting Bugs

When reporting bugs, please include:

1. **A clear title and description**
2. **Steps to reproduce** the issue
3. **Expected behavior** vs actual behavior
4. **Environment details**:
   - Python version
   - AgentHelm version
   - Operating system
   - LLM provider (Mistral/OpenAI)
5. **Code samples** or minimal reproducible example
6. **Error messages** or stack traces
7. **Screenshots** (if applicable)

## Suggesting Enhancements

We love new ideas! When suggesting enhancements:

1. **Check existing issues** to avoid duplicates
2. **Explain the use case** and problem you're solving
3. **Describe your proposed solution**
4. **Consider alternatives** you've thought about
5. **Be open to discussion** about implementation

## Questions?

If you have questions or need help:

- Open a [GitHub Discussion](https://github.com/hadywalied/agenthelm/discussions)
- Open an issue with the `question` label
- Check the [documentation](https://hadywalied.github.io/agenthelm/)

---

Thank you for contributing to AgentHelm! 🚀

Your contributions help make AI agents more observable, reliable, and production-ready for everyone.