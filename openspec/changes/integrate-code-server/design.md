# Design: Code-Server Integration

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser                                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐         ┌──────────────────────────────────┐ │
│  │   Frontend    │         │      Code-Server Tab             │ │
│  │  (Projects)   │         │   (VS Code in Browser)           │ │
│  │               │ ──────► │                                  │ │
│  │ "Open Editor" │  new    │  /project-abc?folder=/workspace  │ │
│  │    button     │  tab    │                                  │ │
│  └───────┬───────┘         └──────────────────────────────────┘ │
│          │                                   │                   │
└──────────┼───────────────────────────────────┼───────────────────┘
           │ API call                          │ WebSocket
           ▼                                   ▼
┌──────────────────────────┐    ┌──────────────────────────────────┐
│      Backend API         │    │        Code-Server               │
│  /api/v1/code-server/    │    │    (codercom/code-server)        │
│                          │    │                                  │
│  - Generate session URL  │    │  Volume mounts:                  │
│  - Validate project      │    │  - /projects:/workspace:rw       │
│  - Track sessions        │    │  - /config:/home/coder/.config   │
└──────────────────────────┘    └──────────────────────────────────┘
```

## Authentication Strategy

### Option A: Shared Password (Simple)
- Single password for all code-server access
- Stored in environment variable `CODE_SERVER_PASSWORD`
- Pro: Simple setup
- Con: No per-user/per-project isolation

### Option B: Token-Based (Recommended) ✓
- Backend generates unique session tokens per project
- Token embedded in URL or cookie
- Code-server configured with `--auth none` but behind authenticated proxy
- Pro: Better security, per-project isolation
- Con: Requires proxy setup

### Chosen Approach: Hybrid
1. Code-server runs with password authentication (fallback)
2. Backend provides direct URL with folder parameter
3. Users authenticate once per browser session
4. Projects isolated by folder parameter

## URL Structure

```
http://localhost:8443/?folder=/workspace/{project_local_path}
```

Example:
- Project "ml-training" with `local_path: /data/projects/ml-training`
- Code-server URL: `http://localhost:8443/?folder=/workspace/ml-training`

## Volume Mounting Strategy

```yaml
code-server:
  volumes:
    # Mount all projects under /workspace
    - ${PROJECTS_ROOT_PATH:-./projects}:/workspace:rw
    # Persist code-server config (extensions, settings)
    - code-server-config:/home/coder/.config
    # Persist workspace states
    - code-server-data:/home/coder/.local/share/code-server
```

### Workspace Isolation
- Each project opens with `?folder=/workspace/{project_path}`
- VS Code workspace settings stored per-folder
- Extensions installed globally but can be workspace-specific

## Security Considerations

### Path Traversal Prevention
```python
def validate_project_path(project_path: str, projects_root: str) -> bool:
    """Ensure project path is within projects root."""
    real_path = os.path.realpath(os.path.join(projects_root, project_path))
    real_root = os.path.realpath(projects_root)
    return real_path.startswith(real_root)
```

### Network Security
- Code-server only accessible via localhost or internal network
- In production: reverse proxy with TLS
- Optional: IP whitelist for code-server port

## Session Management

### Session Lifecycle
1. User clicks "Open Editor" for project
2. Backend validates user permission for project
3. Backend returns code-server URL with folder parameter
4. Frontend opens URL in new tab
5. User authenticates with code-server password (once per session)
6. Code-server loads workspace

### No Active Session Tracking Needed (Simplified)
- Code-server handles its own session management
- Backend only provides URL construction
- No need for complex session tracking

## Configuration

### Environment Variables
```bash
# Code-Server Settings
CODE_SERVER_PORT=8443
CODE_SERVER_PASSWORD=your-secure-password
CODE_SERVER_BIND_ADDR=0.0.0.0:8443

# Projects Root (mounted to code-server)
PROJECTS_ROOT_PATH=./projects
```

### Docker Compose Service
```yaml
code-server:
  image: codercom/code-server:latest
  container_name: mlsm-code-server
  environment:
    - PASSWORD=${CODE_SERVER_PASSWORD:-mlsmanager}
  volumes:
    - ${PROJECTS_ROOT_PATH:-./projects}:/workspace:rw
    - code-server-config:/home/coder/.config
    - code-server-data:/home/coder/.local/share/code-server
  ports:
    - "${CODE_SERVER_PORT:-8443}:8443"
  command: --bind-addr 0.0.0.0:8443 --auth password
  restart: unless-stopped
```

## Frontend Implementation

### Modified Open Editor Flow
```tsx
const handleOpenEditor = async (project: Project) => {
  try {
    // Get code-server URL from backend
    const response = await fetch(`/api/v1/code-server/url/${project.id}`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    
    if (response.ok) {
      const { url } = await response.json();
      // Open in new tab
      window.open(url, `code-server-${project.id}`);
    } else {
      message.error('Failed to open editor');
    }
  } catch (err) {
    message.error('Failed to connect to code-server');
  }
};
```

## Fallback Strategy

If code-server is unavailable:
1. Backend health check returns error
2. Frontend shows error message
3. Option to view project files in read-only mode (existing API)

## Resource Limits (Production)

```yaml
code-server:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '0.5'
        memory: 512M
```
