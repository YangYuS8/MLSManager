# Development Tooling Specification

## ADDED Requirements

### Requirement: Backend Package Management with uv
The backend project SHALL use uv as the Python package manager for dependency resolution and virtual environment management.

#### Scenario: Initialize backend development environment
- **WHEN** a developer runs `uv sync` in the backend directory
- **THEN** all dependencies are installed in a virtual environment

#### Scenario: Add new dependency
- **WHEN** a developer runs `uv add <package>`
- **THEN** the package is added to pyproject.toml and installed

### Requirement: Backend Code Linting with Ruff
The backend project SHALL use ruff for Python code linting and formatting.

#### Scenario: Check code style
- **WHEN** a developer runs `uv run ruff check .` in the backend directory
- **THEN** all Python files are checked for style violations

#### Scenario: Auto-format code
- **WHEN** a developer runs `uv run ruff format .` in the backend directory
- **THEN** all Python files are formatted according to project standards

### Requirement: Frontend Code Linting with ESLint
The frontend project SHALL use ESLint for TypeScript/React code linting.

#### Scenario: Check frontend code style
- **WHEN** a developer runs `pnpm lint` in the frontend directory
- **THEN** all TypeScript/React files are checked for style violations

### Requirement: Frontend Code Formatting with Prettier
The frontend project SHALL use Prettier for code formatting.

#### Scenario: Check frontend formatting
- **WHEN** a developer runs `pnpm format:check` in the frontend directory
- **THEN** all files are checked for formatting consistency

#### Scenario: Auto-format frontend code
- **WHEN** a developer runs `pnpm format` in the frontend directory
- **THEN** all files are formatted according to project standards

### Requirement: Backend CI Quality Check
The system SHALL run automated backend code quality checks via GitHub Actions.

#### Scenario: Backend changes trigger workflow
- **WHEN** a pull request or push modifies files in `backend/**`
- **THEN** the backend quality workflow is triggered

#### Scenario: Non-backend changes skip workflow
- **WHEN** a pull request or push only modifies files outside `backend/**`
- **THEN** the backend quality workflow is NOT triggered

#### Scenario: Backend quality check passes
- **WHEN** the backend workflow runs
- **THEN** it checks code with ruff lint and ruff format --check

### Requirement: Frontend CI Quality Check
The system SHALL run automated frontend code quality checks via GitHub Actions.

#### Scenario: Frontend changes trigger workflow
- **WHEN** a pull request or push modifies files in `frontend/**`
- **THEN** the frontend quality workflow is triggered

#### Scenario: Non-frontend changes skip workflow
- **WHEN** a pull request or push only modifies files outside `frontend/**`
- **THEN** the frontend quality workflow is NOT triggered

#### Scenario: Frontend quality check passes
- **WHEN** the frontend workflow runs
- **THEN** it checks TypeScript types, runs ESLint, and verifies Prettier formatting
