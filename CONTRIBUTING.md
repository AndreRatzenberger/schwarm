# Contributing to Schwarm Framework

Thank you for your interest in contributing to the Schwarm Framework! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct (see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)).

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in the Issues section
2. If not, create a new issue with:
   - A clear title
   - A detailed description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment details

### Suggesting Enhancements

1. Check if the enhancement has been suggested in Issues or Discussions
2. If not, create a new issue with:
   - A clear title
   - Detailed description of the enhancement
   - Use cases and benefits
   - Any potential implementation details

### Pull Requests

1. Fork the repository
2. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes
4. Run tests and ensure they pass:
   ```bash
   pytest
   ```
5. Update documentation if needed
6. Commit your changes:
   ```bash
   git commit -m "feat: add your feature description"
   ```
7. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
8. Create a Pull Request

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/schwarm.git
   cd schwarm
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Project Structure

```
schwarm/
├── schwarm/
│   ├── __init__.py
│   ├── agent.py
│   ├── agent_builder.py
│   ├── context.py
│   ├── events.py
│   ├── function.py
│   ├── provider.py
│   ├── providers/
│   │   └── llm_provider.py
│   └── functions/
│       └── summarize_function.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_agent.py
│   └── ...
├── docs/
│   └── README.md
└── examples/
    └── summarizer_example.py
```

## Coding Standards

### Python Version

- Use Python 3.12 or higher
- Use type hints consistently

### Style Guide

- Follow PEP 8
- Use [Black](https://github.com/psf/black) for code formatting
- Use [Ruff](https://github.com/astral-sh/ruff) for linting

### Type Hints

- Use type hints for all function arguments and return values
- Use `Optional` for optional parameters
- Use `Any` sparingly and only when necessary

### Documentation

- Use Google-style docstrings
- Document all public classes and methods
- Include examples in docstrings where helpful

### Testing

- Write tests for all new features
- Maintain or improve test coverage
- Use pytest fixtures appropriately
- Mock external dependencies

## Git Commit Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or modifying tests
- `chore:` Maintenance tasks

Example:
```
feat: add support for custom provider configurations

This commit adds the ability to configure providers with custom parameters,
allowing for more flexible provider implementations.

- Add configuration interface
- Update provider base class
- Add tests for configuration handling
```

## Creating New Components

### New Providers

1. Create a new file in `schwarm/providers/`
2. Inherit from `Provider` base class
3. Implement required methods
4. Add comprehensive tests
5. Update documentation

### New Functions

1. Create a new file in `schwarm/functions/`
2. Use the `Function` class
3. Implement the function logic
4. Add comprehensive tests
5. Update documentation

## Review Process

1. All code changes require a pull request
2. CI must pass (tests, linting, type checking)
3. At least one maintainer review is required
4. Documentation must be updated if needed
5. Changes should include tests

## Release Process

1. Version numbers follow [Semantic Versioning](https://semver.org/)
2. Changes are documented in CHANGELOG.md
3. Releases are tagged in git
4. Release notes are created on GitHub

## Questions?

- Open a Discussion for general questions
- Open an Issue for bugs or feature requests
- Join our community channels (TBD)

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
