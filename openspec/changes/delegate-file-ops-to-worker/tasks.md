# Tasks: 将文件操作委托给 Worker 节点

## Phase 1: Worker Agent 扩展

### 1.1 文件操作模块
- [x] 创建 `worker/internal/fileops/` 包
- [x] 实现 `fileops.go` - 基础文件操作（创建目录、检查路径安全）
- [x] 实现 `git.go` - Git 操作（clone, pull, status）

### 1.2 Worker API 端点
- [x] `POST /api/v1/projects/clone` - 克隆 Git 仓库
- [x] `POST /api/v1/projects/{id}/pull` - 拉取更新
- [x] `GET /api/v1/projects/{id}/status` - 获取 Git 状态
- [x] `DELETE /api/v1/projects/{id}` - 删除项目目录

### 1.3 Worker HTTP 服务器
- [x] 在 worker agent 中添加 HTTP 服务器
- [x] 配置 `AGENT_API_PORT` 环境变量
- [x] 实现请求认证（使用 agent token）

### 1.4 单元测试
- [ ] 测试 Git clone 功能
- [ ] 测试路径安全检查
- [ ] 测试 API 端点

## Phase 2: Backend 重构

### 2.1 Worker 客户端服务
- [x] 创建 `backend/app/services/worker_client.py`
- [x] 实现 `WorkerClient.clone_project()` 方法
- [x] 实现 `WorkerClient.pull_project()` 方法
- [x] 实现 `WorkerClient.delete_project()` 方法
- [x] 添加错误处理

### 2.2 重构 projects.py
- [x] 修改 `clone_project` 端点 - 委托给 worker
- [x] 修改 `delete_project` 端点 - 通知 worker 删除目录

### 2.3 状态回调 API
- [x] 添加 `POST /api/v1/internal/projects/{id}/status` 端点
- [x] 实现 worker token 验证
- [x] 更新项目状态流转

### 2.4 Node 模型扩展
- [x] 添加 `hostname` 字段
- [x] 添加 `agent_port` 字段
- [x] 添加 `agent_token` 字段

### 2.5 异步任务处理（可选，使用 RabbitMQ）
- [ ] 定义克隆任务消息格式
- [ ] Worker 监听任务队列
- [ ] Backend 发布任务到队列
- [ ] 实现任务超时和重试

## Phase 3: 前端适配

### 3.1 状态轮询
- [ ] 克隆操作提交后显示进度状态
- [ ] 轮询项目状态直到完成/失败
- [ ] 显示错误信息（如果失败）

### 3.2 节点状态检查
- [ ] 克隆前检查目标节点是否在线
- [ ] 节点离线时禁用克隆按钮
- [ ] 提示用户选择在线节点

## Phase 4: 清理和文档

### 4.1 代码清理
- [ ] 移除 backend 中 `get_projects_root()` 函数（保留用于向后兼容）
- [ ] 移除 backend 中 `run_git_command()` 函数（保留用于本地 git 操作）

### 4.2 配置更新
- [x] 更新 `infra/dev/.env.worker.example`
- [x] 更新 `infra/prod/.env.worker.example`
- [x] 确保 `AGENT_PROJECTS_PATH=/data/projects`

### 4.3 文档更新
- [ ] 更新 `README.md` - 架构说明
- [ ] 更新 `infra/README.md` - 配置说明
- [ ] 添加 Worker API 文档

## Verification Checklist

- [ ] 从 GitHub 克隆项目成功
- [ ] 项目文件出现在 worker 节点的 `/data/projects/` 目录
- [ ] 项目状态正确更新（PENDING → SYNCING → ACTIVE/ERROR）
- [ ] 前端正确显示克隆进度和结果
- [ ] code-server 可以访问克隆的项目文件
- [ ] 删除项目时同时删除文件目录
- [ ] Worker 离线时前端正确提示
