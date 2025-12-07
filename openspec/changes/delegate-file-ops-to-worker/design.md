# Design: 将文件操作委托给 Worker 节点

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                         Master Node                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │ Frontend │───▶│ Backend  │───▶│ RabbitMQ │    │ Postgres │   │
│  │ (React)  │◀───│ (FastAPI)│◀───│  (Tasks) │    │   (DB)   │   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│                         │                                        │
└─────────────────────────┼───────────────────────────────────────┘
                          │ HTTP/AMQP
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Worker Node(s)                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Worker Agent (Go)                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │  │ Executor │  │ Scanner  │  │ FileOps  │  │ HTTP API │   │  │
│  │  │  (Jobs)  │  │ (Datasets)│ │ (Git/FS) │  │ (:8081)  │   │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │                    /data (Volume)                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │  │ projects │  │ datasets │  │   jobs   │  │ outputs  │   │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │                   Code-Server (:8443)                      │  │
│  │               workspace = /data/projects                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Worker Agent 扩展设计

### 目录结构

```
worker/
├── cmd/
│   └── agent/
│       └── main.go              # 入口，启动 HTTP 服务器
├── internal/
│   ├── api/                     # 新增：HTTP API
│   │   ├── server.go            # HTTP 服务器
│   │   ├── middleware.go        # 认证中间件
│   │   └── routes.go            # 路由注册
│   ├── fileops/                 # 新增：文件操作
│   │   ├── fileops.go           # 文件系统操作
│   │   ├── git.go               # Git 操作
│   │   └── handler.go           # HTTP 处理器
│   ├── client/                  # 已有：Master 客户端
│   ├── config/                  # 已有：配置
│   ├── executor/                # 已有：作业执行
│   └── scanner/                 # 已有：数据集扫描
```

### HTTP API 设计

```go
// worker/internal/api/server.go
package api

import (
    "net/http"
    "github.com/gin-gonic/gin"
)

type Server struct {
    router  *gin.Engine
    config  *config.Config
    fileops *fileops.Handler
}

func NewServer(cfg *config.Config) *Server {
    s := &Server{
        router:  gin.Default(),
        config:  cfg,
        fileops: fileops.NewHandler(cfg),
    }
    s.setupRoutes()
    return s
}

func (s *Server) setupRoutes() {
    // 认证中间件
    api := s.router.Group("/api/v1", s.authMiddleware)
    
    // 项目/文件操作
    projects := api.Group("/projects")
    {
        projects.POST("/clone", s.fileops.CloneProject)
        projects.POST("/:id/pull", s.fileops.PullProject)
        projects.GET("/:id/status", s.fileops.GetProjectStatus)
        projects.DELETE("/:id", s.fileops.DeleteProject)
    }
}

func (s *Server) authMiddleware(c *gin.Context) {
    token := c.GetHeader("X-Agent-Token")
    if token != s.config.AgentToken {
        c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
        return
    }
    c.Next()
}

func (s *Server) Run(addr string) error {
    return s.router.Run(addr)
}
```

### Git 操作实现

```go
// worker/internal/fileops/git.go
package fileops

import (
    "context"
    "os/exec"
    "path/filepath"
    "strings"
)

type CloneRequest struct {
    ProjectID  int64  `json:"project_id" binding:"required"`
    GitURL     string `json:"git_url" binding:"required"`
    Branch     string `json:"branch"`
    TargetPath string `json:"target_path" binding:"required"`
}

type CloneResponse struct {
    ProjectID int64  `json:"project_id"`
    Success   bool   `json:"success"`
    Message   string `json:"message,omitempty"`
    LocalPath string `json:"local_path,omitempty"`
}

type Handler struct {
    config       *config.Config
    masterClient *client.MasterClient
}

func NewHandler(cfg *config.Config, mc *client.MasterClient) *Handler {
    return &Handler{
        config:       cfg,
        masterClient: mc,
    }
}

func (h *Handler) CloneProject(c *gin.Context) {
    var req CloneRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    
    // 1. 构建完整路径
    fullPath := filepath.Join(h.config.ProjectsPath, req.TargetPath)
    
    // 2. 安全检查（防止路径穿越）
    cleanPath := filepath.Clean(fullPath)
    if !strings.HasPrefix(cleanPath, h.config.ProjectsPath) {
        c.JSON(http.StatusBadRequest, gin.H{"error": "invalid target path"})
        return
    }
    
    // 3. 创建父目录
    if err := os.MkdirAll(filepath.Dir(fullPath), 0755); err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    
    // 4. 异步执行 git clone
    go h.doClone(req, fullPath)
    
    // 5. 立即返回接受状态
    c.JSON(http.StatusAccepted, CloneResponse{
        ProjectID: req.ProjectID,
        Success:   true,
        Message:   "Clone started",
        LocalPath: fullPath,
    })
}

func (h *Handler) doClone(req CloneRequest, fullPath string) {
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
    defer cancel()
    
    // 构建 git clone 命令
    args := []string{"clone", "--progress"}
    if req.Branch != "" {
        args = append(args, "--branch", req.Branch)
    }
    args = append(args, req.GitURL, fullPath)
    
    cmd := exec.CommandContext(ctx, "git", args...)
    output, err := cmd.CombinedOutput()
    
    // 回调 master 更新状态
    status := "ACTIVE"
    message := ""
    if err != nil {
        status = "ERROR"
        message = string(output)
    }
    
    h.masterClient.UpdateProjectStatus(ctx, req.ProjectID, status, message)
}
```

## Backend 重构设计

### Worker 客户端服务

```python
# backend/app/services/worker_client.py
import httpx
from app.models.node import Node

class WorkerClient:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
    
    async def clone_project(
        self,
        node: Node,
        project_id: int,
        git_url: str,
        branch: str,
        target_path: str,
    ) -> bool:
        """Send clone request to worker node."""
        url = f"http://{node.hostname}:{node.agent_port}/api/v1/projects/clone"
        headers = {"X-Agent-Token": node.agent_token}
        payload = {
            "project_id": project_id,
            "git_url": git_url,
            "branch": branch,
            "target_path": target_path,
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                return response.status_code == 202  # Accepted
            except httpx.RequestError as e:
                raise WorkerUnreachableError(f"Cannot reach worker: {e}")
    
    async def check_node_online(self, node: Node) -> bool:
        """Check if worker node is reachable."""
        url = f"http://{node.hostname}:{node.agent_port}/health"
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url)
                return response.status_code == 200
            except httpx.RequestError:
                return False


class WorkerUnreachableError(Exception):
    """Worker node is not reachable."""
    pass
```

### 重构后的 projects.py

```python
# backend/app/api/v1/endpoints/projects.py (重构后)

from app.services.worker_client import WorkerClient, WorkerUnreachableError

worker_client = WorkerClient()

@router.post("/clone", response_model=ProjectRead, status_code=status.HTTP_202_ACCEPTED)
async def clone_project(
    clone_request: ProjectCloneRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> Project:
    """Clone a git repository as a new project (delegated to worker)."""
    # 1. 验证节点存在
    node = await get_node_or_404(db, clone_request.node_id)
    
    # 2. 检查节点是否在线
    if not await worker_client.check_node_online(node):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker node is offline",
        )
    
    # 3. 生成目标路径（相对于 worker 的 AGENT_PROJECTS_PATH）
    target_path = f"{current_user.id}_{clone_request.name}"
    
    # 4. 创建项目记录（状态：PENDING）
    project = Project(
        name=clone_request.name,
        description=clone_request.description,
        git_url=clone_request.git_url,
        git_branch=clone_request.git_branch,
        local_path=target_path,  # 存储相对路径
        node_id=clone_request.node_id,
        owner_id=current_user.id,
        status=ProjectStatus.PENDING.value,
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    # 5. 发送克隆请求给 worker（异步）
    try:
        await worker_client.clone_project(
            node=node,
            project_id=project.id,
            git_url=clone_request.git_url,
            branch=clone_request.git_branch,
            target_path=target_path,
        )
        project.status = ProjectStatus.SYNCING.value
        await db.commit()
    except WorkerUnreachableError:
        project.status = ProjectStatus.ERROR.value
        project.sync_error = "Worker unreachable"
        await db.commit()
    
    return project
```

### 状态回调端点

```python
# backend/app/api/v1/endpoints/internal.py

from fastapi import APIRouter, Depends, HTTPException, Header
from app.api.deps import DbSession
from app.models.project import Project, ProjectStatus
from app.models.node import Node

router = APIRouter()

@router.post("/projects/{project_id}/status")
async def update_project_status(
    project_id: int,
    status: str,
    message: str = "",
    db: DbSession,
    x_agent_token: str = Header(...),
):
    """Worker callback to update project status."""
    # 验证 token
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    node = await db.get(Node, project.node_id)
    if not node or node.agent_token != x_agent_token:
        raise HTTPException(status_code=401, detail="Invalid agent token")
    
    # 更新状态
    project.status = status
    if message:
        project.sync_error = message
    if status == ProjectStatus.ACTIVE.value:
        project.last_sync_at = datetime.now(timezone.utc)
    
    await db.commit()
    return {"success": True}
```

## 配置更新

### Worker 环境变量

```env
# infra/dev/.env.worker.example
AGENT_NODE_NAME=worker-001
AGENT_MASTER_URL=http://host.docker.internal:8000
AGENT_API_PORT=8081                     # 新增：Worker HTTP API 端口

# 存储路径
AGENT_STORAGE_PATH=/data
AGENT_PROJECTS_PATH=/data/projects      # Git clone 目标目录
AGENT_DATASETS_PATH=/data/datasets
AGENT_JOBS_WORKSPACE=/data/jobs
```

### Node 模型更新

```python
# backend/app/models/node.py
class Node(Base):
    # ... existing fields ...
    agent_port: Mapped[int | None] = mapped_column(Integer, default=8081)
    agent_token: Mapped[str | None] = mapped_column(String(255))
```

## 安全考虑

1. **路径安全**：所有文件操作必须检查路径是否在允许范围内
2. **认证**：Worker API 使用 token 认证
3. **网络隔离**：Worker API 端口不对外暴露
4. **资源限制**：Git clone 设置超时，防止资源耗尽
