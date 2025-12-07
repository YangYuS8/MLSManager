# Change Proposal: Code-Server Integration Fixes

## Summary
Fix multiple issues discovered during code-server integration testing:
1. Makefile code-server service commands
2. Password authentication flow  
3. Project deletion not removing local files
4. Missing status translations
5. Invalid project path error

## Scope

### 1. Makefile Integration
- Add code-server to services group
- Add dedicated commands for code-server management

### 2. Authentication Improvement
- Switch from password to `--auth=none` for development
- Keep password auth option for production

### 3. Project Deletion Fix
- Current: `delete_files=false` by default, UI doesn't pass `true`
- Fix: Add checkbox in delete confirmation or always delete files

### 4. Translation Fix
- `projects.status` is an object, not a string
- Remove the erroneous column or fix the reference

### 5. Path Validation Fix
- `validate_project_path()` fails because project path doesn't exist yet
- Fix path validation logic

## Risk Assessment
- **Low Risk**: All changes are isolated to specific components
- **No Breaking Changes**: Backwards compatible

## Success Criteria
- [ ] code-server starts via `make services`
- [ ] No password required in development mode
- [ ] Project files deleted when project is deleted
- [ ] No translation errors on projects page
- [ ] "Open Editor" works correctly
