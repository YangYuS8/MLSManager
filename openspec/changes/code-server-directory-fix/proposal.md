# Change Proposal: Fix Code-Server Project Directory Alignment

## Summary
Fix two issues preventing code-server from properly accessing and managing project files:
1. Project storage path doesn't align with code-server's mounted workspace
2. File permission issues preventing extension installation

## Problem Analysis

### Issue 1: Path Mismatch
- Projects are created at: `node.storage_path` (e.g., `/data/projects/1_myproject`)
- Code-server mounts: `./projects` → `/home/coder/workspace`
- These paths never intersect, so projects are invisible to code-server

### Issue 2: Permission Problems
- Code-server runs as `coder` user (uid 1000)
- Host directories may be owned by different users
- Extensions and settings can't be saved due to permission denied

## Proposed Solution

### Solution for Path Alignment
1. **Use PROJECTS_ROOT_PATH consistently**:
   - Backend should use `PROJECTS_ROOT_PATH` env var for project storage
   - Projects created under this path will be visible in code-server
   - Path structure: `./projects/{user_id}_{project_name}/`

2. **Update project creation logic**:
   - Change default base path from `node.storage_path` to `PROJECTS_ROOT_PATH`
   - Ensure created paths are relative to the shared projects directory

### Solution for Permissions
1. **Add user configuration to code-server container**:
   - Map container user to host user's UID/GID
   - Or create directories with proper permissions beforehand

2. **Use environment variables for UID/GID**

## Risk Assessment
- **Medium Risk**: Changes project storage location
- **Migration**: Existing projects may need to be re-created or moved

## Success Criteria
- [ ] New projects visible in code-server workspace
- [ ] Can install extensions in code-server
- [ ] Can create/edit files within projects
