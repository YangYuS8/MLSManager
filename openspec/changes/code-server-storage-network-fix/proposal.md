# Change Proposal: Fix Code-Server Network and Storage Issues

## Summary
Fix code-server integration based on correct multi-node architecture understanding:
1. Remove proxy settings that break extension installation
2. Deploy code-server alongside worker (per-node), NOT on master
3. Share storage paths between code-server and worker

## Architecture Clarification

### Correct Architecture
```
┌─────────────────────────────────────────┐
│  Master Node                            │
│  ├─ backend (FastAPI API server)        │
│  ├─ frontend (React UI)                 │
│  ├─ db (PostgreSQL)                     │
│  └─ rabbitmq                            │
└─────────────────────────────────────────┘
           │
           │ HTTP API / Message Queue
           ▼
┌─────────────────────────────────────────┐
│  Worker Node 1                          │
│  ├─ worker (Go agent)             │
│  ├─ code-server (VS Code in browser)    │  ← Code-server per worker!
│  ├─ ./data/projects/  ─────────────────────► Shared project storage
│  └─ ./data/datasets/  ─────────────────────► Shared dataset storage
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Worker Node 2                          │
│  ├─ worker                        │
│  ├─ code-server                         │
│  ├─ ./data/projects/                    │
│  └─ ./data/datasets/                    │
└─────────────────────────────────────────┘
```

### Key Points
- code-server runs on EACH worker node, not on master
- Each worker's code-server shares storage with its worker
- Frontend opens code-server URL pointing to the specific worker node
- Use bind mounts (relative paths), NOT named volumes

## Implementation Summary

### Files Changed

#### Removed from Master Node
- `docker-compose.dev.yml`: Removed code-server and worker services
- `docker-compose.yml`: Removed code-server and worker services

#### New Worker Node Deployment
- `infra/docker-compose.worker.yml`: Production worker (agent + code-server)
- `infra/docker-compose.worker.dev.yml`: Development worker with hot-reload
- `infra/.env.worker.example`: Production environment template
- `infra/.env.worker.dev.example`: Development environment template

#### Backend Changes
- `app/models/node.py`: Added `code_server_port` field to Node model
- `app/schemas/node.py`: Added `code_server_port` to NodeRead schema
- `app/api/v1/endpoints/code_server.py`: Updated to return node-specific code-server URL
- `worker/internal/config/config.go`: Added `AGENT_PROJECTS_PATH` config

#### Updated Configuration
- `Makefile`: Added worker commands, updated help text, fixed local-worker paths
- `.gitignore`: Added `/data/` and worker env files

### Storage Structure
```
./data/                          # Worker node data root
├── projects/                    # Git clones, user code (shared with code-server)
├── datasets/                    # Dataset files
├── jobs/                        # Job workspaces and outputs
├── .ml-agent/                   # Agent token storage
└── .code-server/               # Code-server config and data
    ├── config/
    └── data/
```

## Usage

### Development (Single Machine)
```bash
# Terminal 1: Start master services
make services-up && make local-backend

# Terminal 2: Start frontend
make local-frontend

# Terminal 3: Start worker + code-server
make local-worker
# And in another terminal:
make local-codeserver
```

### Production (Multi-Node)
```bash
# On Master Node:
make prod-up

# On each Worker Node:
# 1. Copy infra/ directory
# 2. Configure infra/.env.worker
# 3. Run:
make worker-up
```

## Risk Assessment
- **Medium Risk**: Architecture change
- **Database Migration**: Need to add `code_server_port` column to `nodes` table

## Success Criteria
- [x] code-server removed from master compose files
- [x] Worker-specific compose files created
- [x] code-server runs on worker nodes
- [x] code-server shares storage with worker
- [x] Backend API returns node-specific code-server URL
- [ ] Test: code-server can install extensions (no proxy errors)
- [ ] Test: code-server workspace shows worker's projects
