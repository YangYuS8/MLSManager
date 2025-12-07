# Implementation Tasks

## Task 1: Makefile Integration
- [x] Add code-server to `services` and `services-up` targets
- [x] Add `dev-logs-codeserver` command
- [x] Add `dev-restart-codeserver` command

## Task 2: Disable Password Auth (Development)
- [x] Update docker-compose.dev.yml to use `--auth=none`
- [x] Keep password auth in docker-compose.yml (production)
- [x] Update port mapping from 8080 to 8000 (code-server 4.x default)

## Task 3: Fix Project Deletion
- [x] Change default of `delete_files` from False to True
- [x] Update frontend to not pass explicit false parameter

## Task 4: Fix Translation Error
- [x] Found: `projects.status` used both as string and object
- [x] Changed column title to use `common.status`
- [x] Removed redundant string `projects.status` from locales

## Task 5: Fix Path Validation
- [x] Rewrote `validate_project_path()` to only check for traversal attacks
- [x] Added `get_project_workspace_path()` to extract basename from local_path
- [x] Removed dependency on PROJECTS_ROOT_PATH matching project paths
