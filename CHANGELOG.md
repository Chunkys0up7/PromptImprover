# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2023-12-26

### Added
- Unified prompt engineering platform built with Streamlit.
- Core features: Prompt creation, interactive testing, DSPy optimization, and versioning.
- Multi-page app structure with a main landing page and a "Manager" page.
- Professional UI styling with custom CSS.
- Dialog-based workflows for testing and viewing lineage.
- Persistent state via a local SQLite database.
- Comprehensive documentation including a `README.md`, database migration guide, and LLM provider guide.
- `pytest` testing framework with initial tests for database operations.
- `CONTRIBUTING.md` and `CHANGELOG.md`.

### Changed
- Migrated the entire application from a dual Chainlit/Streamlit setup to a single, unified Streamlit application.
- Refactored all modules for better separation of concerns, configuration management, and exception handling.
- Replaced manual service initialization with `@st.cache_resource` for improved performance.
- Updated database access logic to use modern SQLAlchemy syntax.

### Removed
- All Chainlit-related files and dependencies.
- Old, outdated documentation and backup files.
- Redundant logic from the main `streamlit_app.py` file.

## [0.1.0] - 2023-12-20

### Added
- Initial proof-of-concept using Chainlit and Streamlit.
- Basic prompt generation and API client. 