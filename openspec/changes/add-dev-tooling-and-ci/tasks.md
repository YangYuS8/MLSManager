# Implementation Tasks

## 1. Backend: uv Setup
- [x] 1.1 Create `backend/pyproject.toml` with project metadata and dependencies
- [x] 1.2 Add ruff configuration in `backend/ruff.toml`
- [x] 1.3 Remove old `backend/requirements.txt` (replaced by pyproject.toml)
- [x] 1.4 Update `backend/Dockerfile` to use uv

## 2. Frontend: Linting Setup
- [x] 2.1 Update `frontend/eslint.config.js` with strict TypeScript rules
- [x] 2.2 Create `frontend/.prettierrc` configuration
- [x] 2.3 Add lint/format scripts to `frontend/package.json`

## 3. GitHub Actions Workflows
- [x] 3.1 Create `.github/workflows/backend-quality.yml` with path filter for `backend/**`
- [x] 3.2 Create `.github/workflows/frontend-quality.yml` with path filter for `frontend/**`

## 4. Documentation
- [x] 4.1 Update `AGENTS.md` with new development commands
- [x] 4.2 Update `README.md` with linting/formatting instructions
