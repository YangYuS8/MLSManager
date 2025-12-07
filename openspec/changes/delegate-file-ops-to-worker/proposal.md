# Change: 将文件操作委托给 Worker 节点

## Status: 🟢 实施中 (Phase 1-2 完成)

## Why

当前系统中，从 GitHub 克隆项目等文件操作是由 backend（master 节点）直接执行的，文件下载到 `backend/projects` 目录。这存在以下问题：

1. **架构不合理**：在多节点架构中，文件应该存储在目标 worker 节点上，而不是 master 节点
2. **扩展性差**：当有多个 worker 节点时，master 无法直接操作远程节点的文件系统
3. **路径不一致**：当前使用 `./projects` 或 `PROJECTS_ROOT_PATH`，但正确路径应该是 `data/projects`（与 code-server workspace 对齐）
4. **职责混乱**：master 应该是协调者，具体的文件操作应该由 worker agent 执行

## What Changes

### 1. Worker Agent 扩展

扩展 Go worker agent 以支持文件管理操作：

```
worker/internal/
├── fileops/           # 新增：文件操作模块
│   ├── fileops.go     # 文件操作核心逻辑
│   ├── git.go         # Git 克隆/拉取/同步
│   └── handler.go     # HTTP 处理器
```

新增 Worker API 端点：
- `POST /api/v1/projects/clone` - 克隆 Git 仓库
- `POST /api/v1/projects/pull` - 拉取更新
- `GET /api/v1/projects/{id}/status` - 获取项目状态
- `DELETE /api/v1/projects/{id}` - 删除项目目录

### 2. Backend API 重构

将 `clone_project` 从直接执行改为委托给 worker：

```python
# 当前实现（直接执行）
subprocess.run(["git", "clone", ...])

# 重构后（委托给 worker）
await worker_client.clone_project(node_id, git_url, branch, target_path)
```

核心改动：
- 移除 `backend/app/api/v1/endpoints/projects.py` 中的 git 操作
- 新增 worker 客户端服务 `backend/app/services/worker_client.py`
- 项目状态由 worker 通过心跳/回调更新

### 3. 路径标准化

统一所有文件存储到 `data/` 目录：

```
data/                    # 主数据目录（每个节点独立）
├── projects/           # 项目文件（git clone 目标）
├── datasets/           # 数据集
├── jobs/               # 作业工作区
└── outputs/            # 输出文件
```

Worker 配置：
```env
AGENT_STORAGE_PATH=/data
AGENT_PROJECTS_PATH=/data/projects    # Git clone 目标目录
AGENT_DATASETS_PATH=/data/datasets
AGENT_JOBS_WORKSPACE=/data/jobs
```

### 4. 通信流程

```
用户请求克隆项目 → Frontend
       ↓
  POST /api/v1/projects/clone → Backend (master)
       ↓
  1. 验证权限
  2. 创建项目记录 (status=PENDING)
  3. 发送任务给 Worker
       ↓
  Worker Agent 执行 git clone → /data/projects/{user_id}_{project_name}
       ↓
  Worker 回报状态 → Backend 更新项目状态
       ↓
  Frontend 轮询/WebSocket 获取状态更新
```

## Technical Design

### Worker 端实现

```go
// worker/internal/fileops/git.go
type CloneRequest struct {
    ProjectID   int64  `json:"project_id"`
    GitURL      string `json:"git_url"`
    Branch      string `json:"branch"`
    TargetPath  string `json:"target_path"`  // 相对于 AGENT_PROJECTS_PATH
}

type CloneResult struct {
    ProjectID int64  `json:"project_id"`
    Success   bool   `json:"success"`
    Message   string `json:"message,omitempty"`
    LocalPath string `json:"local_path"`
}

func (h *Handler) CloneProject(ctx context.Context, req CloneRequest) (*CloneResult, error) {
    // 1. 构建完整路径
    fullPath := filepath.Join(h.config.ProjectsPath, req.TargetPath)
    
    // 2. 安全检查（防止路径穿越）
    if !strings.HasPrefix(fullPath, h.config.ProjectsPath) {
        return nil, errors.New("invalid target path")
    }
    
    // 3. 执行 git clone
    cmd := exec.CommandContext(ctx, "git", "clone", "--branch", req.Branch, req.GitURL, fullPath)
    output, err := cmd.CombinedOutput()
    
    // 4. 返回结果
    return &CloneResult{
        ProjectID: req.ProjectID,
        Success:   err == nil,
        Message:   string(output),
        LocalPath: fullPath,
    }, nil
}
```

### Backend 端实现

```python
# backend/app/services/worker_client.py
class WorkerClient:
    async def clone_project(
        self, 
        node: Node, 
        project_id: int,
        git_url: str, 
        branch: str, 
        target_path: str
    ) -> bool:
        """Send clone request to worker node."""
        url = f"http://{node.hostname}:{node.agent_port}/api/v1/projects/clone"
        payload = {
            "project_id": project_id,
            "git_url": git_url,
            "branch": branch,
            "target_path": target_path,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            return response.status_code == 200
```

### 状态更新机制

两种方式（可以同时支持）：

1. **轮询**：Frontend 轮询 backend，backend 查询数据库
2. **回调**：Worker 完成后主动回调 backend 更新状态

```python
# backend API：Worker 回调端点
@router.post("/projects/{project_id}/status")
async def update_project_status(
    project_id: int,
    status_update: ProjectStatusUpdate,
    db: DbSession,
):
    """Worker callback to update project status."""
    # 验证请求来自合法 worker（通过 token）
    # 更新项目状态
```

## Migration Plan

### Phase 1: Worker 端准备
1. 在 worker agent 中添加 fileops 模块
2. 实现 git clone/pull 功能
3. 添加 HTTP API 端点
4. 测试独立运行

### Phase 2: Backend 重构
1. 添加 WorkerClient 服务
2. 修改 clone_project 端点，委托给 worker
3. 添加状态回调端点
4. 更新项目状态流转逻辑

### Phase 3: 清理
1. 移除 backend 中的 git 操作代码
2. 移除 backend 对 PROJECTS_ROOT_PATH 的依赖
3. 更新文档和配置示例

## Risks & Mitigations

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Worker 不在线 | 克隆失败 | 前端提示节点离线，禁用克隆按钮 |
| 网络延迟 | 状态更新慢 | 使用乐观 UI + 轮询 |
| Worker 崩溃 | 任务丢失 | 使用任务队列（RabbitMQ）持久化 |
| Git 操作超时 | 大仓库克隆失败 | Worker 端设置合理超时，支持断点续传 |

## Out of Scope

- 文件浏览/编辑功能（已有 file-management 提案）
- WebSocket 实时状态推送（可后续优化）
- 分布式文件同步（跨节点）
