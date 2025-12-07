# Proposal: Integrate Code-Server for Project Editing

## Change ID
`integrate-code-server`

## Summary
Replace the built-in Monaco Editor in project management with code-server (VS Code in browser), providing a full-featured IDE experience for editing project files. Each project will have an isolated workspace with independent extensions and settings.

## Motivation
The current Monaco Editor implementation has limitations:
- Single file editing only, no file tree navigation
- No terminal integration
- No extension support
- Limited language support and IntelliSense

Code-server provides:
- Full VS Code experience in browser
- File explorer with project tree
- Integrated terminal
- Extension marketplace support
- Workspace isolation per project

## Scope

### In Scope
- Add code-server as a Docker service
- Create backend API for managing code-server sessions
- Modify frontend to open code-server in new browser tab
- Implement workspace isolation (one workspace per project)
- Secure access with authentication tokens
- Volume mounting for project directories

### Out of Scope
- Code-server extension auto-installation
- Custom theme/settings sync
- Multi-user collaborative editing
- GPU passthrough for ML extensions

## Affected Capabilities
- **projects**: Project editor UI changes
- **infrastructure**: New Docker service

## Breaking Changes
- **UI Change**: "Open Editor" button now opens new browser tab instead of embedded editor
- **Removed Component**: `ProjectEditor.tsx` will be deprecated (kept for reference but not used)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Resource consumption | High memory usage per session | Implement session timeout and cleanup |
| Security | Unauthorized access to files | Token-based authentication, path restrictions |
| Port conflicts | Multiple code-server instances | Dynamic port allocation or path-based routing |

## Success Criteria
- [ ] User can click "Open Editor" and access code-server in new tab
- [ ] Each project's workspace is isolated
- [ ] Only files within project root are accessible
- [ ] Sessions are properly authenticated
- [ ] Inactive sessions are cleaned up

## Timeline
- **Phase 1**: Docker service setup + basic integration (2 hours)
- **Phase 2**: Authentication and session management (1 hour)
- **Phase 3**: Frontend integration and testing (1 hour)

## Approval
- [ ] Technical review completed
- [ ] Security review completed (token auth, path isolation)
- [ ] Ready for implementation
