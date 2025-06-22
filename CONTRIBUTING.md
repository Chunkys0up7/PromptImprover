# Contributing to the Prompt Engineering Platform

First off, thank you for considering contributing! This project is a community effort, and we welcome any contributions that help make it better.

This document provides guidelines for contributing to the project to ensure a smooth and consistent development process.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

If you find a bug, please open an issue and provide the following information:
- A clear and descriptive title.
- A step-by-step description of how to reproduce the bug.
- The expected behavior and what actually happened.
- Your environment details (OS, Python version, etc.).

### Suggesting Enhancements

If you have an idea for a new feature or an improvement to an existing one, please open an issue to discuss it. This allows us to coordinate efforts and ensure the feature aligns with the project's goals.

### Pull Requests

We welcome pull requests! To submit one, please follow these steps:

1.  **Fork the repository** and create your branch from `main`.
2.  **Set up your environment**:
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt # Or install black, pytest, etc. manually
    ```
3.  **Make your changes**. Ensure you follow the code style guidelines below.
4.  **Add tests** for your changes. We aim for high test coverage to maintain stability.
5.  **Ensure all tests pass**:
    ```bash
    pytest
    ```
6.  **Format your code** with `black`:
    ```bash
    black .
    ```
7.  **Commit your changes** with a clear and descriptive commit message.
8.  **Push to your fork** and submit a pull request to the `main` branch of the upstream repository.

## Development Guidelines

### Code Style

- We use **`black`** for automatic code formatting. Please run it on your code before committing.
- We follow **PEP 8** guidelines for all Python code.
- Imports should be sorted and grouped (standard library, third-party, local modules).

### Testing

- All new features and bug fixes must include corresponding tests.
- We use **`pytest`** as our testing framework.
- Unit tests should be small and focused on a single piece of functionality.
- Mocks and fixtures should be used to isolate tests from external services (like APIs and databases). Use the fixtures provided in `tests/conftest.py`.

### Branching Strategy

We follow a simple branching strategy:
- The `main` branch is the primary development branch and should always be stable.
- All new work should be done in a feature branch, created from `main`.
- Feature branch names should be descriptive (e.g., `feat/add-bedrock-client`, `fix/lineage-view-bug`).
- Once a feature is complete and tests are passing, open a pull request to merge it into `main`.

Thank you again for your contribution! 