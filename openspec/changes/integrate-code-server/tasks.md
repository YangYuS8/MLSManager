# Implementation Tasks

## Phase 1: Infrastructure Setup

- [x] **1.1** Add code-server service to `docker-compose.dev.yml`
  - Use `codercom/code-server:latest` image
  - Configure volume mounts for projects directory
  - Set up environment variables for authentication
  - Configure network settings

- [x] **1.2** Add code-server service to `docker-compose.yml` (production)
  - Same configuration as dev with production optimizations
  - Resource limits (memory/cpu)

- [x] **1.3** Update `.env.dev` and `.env.example` with code-server settings
  - `CODE_SERVER_PASSWORD` or `CODE_SERVER_HASHED_PASSWORD`
  - `CODE_SERVER_PORT`
  - `PROJECTS_ROOT_PATH`

## Phase 2: Backend API

- [x] **2.1** Create `code_server.py` endpoint module
  - `GET /api/v1/code-server/status` - Check code-server status
  - `GET /api/v1/code-server/url/{project_id}` - Get session URL
  - `GET /api/v1/code-server/url/path/{path}` - Get URL by path

- [x] **2.2** Implement path validation
  - Prevent path traversal attacks
  - Validate project paths are within projects root

- [x] **2.3** Register router in `api/v1/router.py`

## Phase 3: Frontend Integration

- [x] **3.1** Update `Projects/index.tsx`
  - Modify "Open Editor" button to call session API
  - Open code-server URL in new browser tab
  - Show loading state while session initializes

- [x] **3.2** Update localization files
  - Add new translation keys for code-server features
  - `openingEditor`, `editorOpened`, `editorFailed`

## Phase 4: Testing & Documentation

- [x] **4.1** Test code-server integration
  - Verify workspace isolation
  - Test authentication flow
  - Test file operations within project bounds

- [x] **4.2** Commit all changes

## Dependencies
- Docker image: `codercom/code-server:latest`
- Projects must have `local_path` defined on the node running code-server
