# Change: Add Development Tooling and CI Workflows

## Status: ✅ 已完成

## Why
The project needs standardized development tooling and automated code quality checks to ensure consistent code style, catch issues early, and maintain high code quality across the team.

## What Changes
- Backend: Switch from pip/venv to uv for faster, more reliable Python dependency management
- Backend: Add ruff for linting and formatting Python code
- Frontend: Add ESLint and Prettier configuration for TypeScript/React code quality
- CI: Add GitHub Actions workflow for frontend code quality (triggered on frontend changes)
- CI: Add GitHub Actions workflow for backend code quality (triggered on backend changes)

## Impact
- Affected specs: New `dev-tooling` capability
- Affected code:
  - `backend/pyproject.toml` (new, replaces requirements.txt for uv)
  - `backend/ruff.toml` (new)
  - `frontend/eslint.config.js` (new/update)
  - `frontend/.prettierrc` (new)
  - `.github/workflows/frontend-quality.yml` (new)
  - `.github/workflows/backend-quality.yml` (new)
  - `AGENTS.md` (update commands section)
