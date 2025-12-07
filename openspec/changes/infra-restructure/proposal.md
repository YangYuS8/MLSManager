# Change Proposal: Infrastructure Restructure

## Status: ✅ COMPLETED

## Summary
重构项目基础设施配置：
1. 将所有容器编排文件移至 `infra/` 目录，按 `dev/` 和 `prod/` 区分环境
2. 生产环境使用 Podman 配置，为后续迁移 K8s 做铺垫
3. 简化 Makefile，只保留开发模式和生产模式

## Current Structure (已删除)
```
/
├── docker-compose.yml          # ❌ 已删除
├── docker-compose.dev.yml      # ❌ 已删除
├── infra/
│   ├── docker-compose.worker.yml      # ❌ 已删除
│   ├── docker-compose.worker.dev.yml  # ❌ 已删除
│   ├── .env.worker.example            # ❌ 已删除
│   └── .env.worker.dev.example        # ❌ 已删除
└── ...
```

## New Structure (已实施)
```
/
├── infra/
│   ├── dev/                           # ✅ 开发环境 (Docker Compose)
│   │   ├── master.yml                 # Master: db + rabbitmq
│   │   ├── worker.yml                 # Worker: code-server
│   │   ├── .env.master.example
│   │   └── .env.worker.example
│   ├── prod/                          # ✅ 生产环境 (Podman)
│   │   ├── master.yml                 # Master: 全部服务
│   │   ├── worker.yml                 # Worker: agent + code-server
│   │   ├── .env.master.example
│   │   └── .env.worker.example
│   └── README.md                      # 部署说明
├── data/                              # ✅ 统一数据目录
│   ├── postgres/
│   ├── rabbitmq/
│   ├── projects/
│   ├── datasets/
│   ├── jobs/
│   ├── .ml-agent/
│   └── .code-server/
├── Makefile                           # ✅ 简化后
└── ...
```

## Development Mode (开发模式)

### Master Node
- **本地热重载**: backend (uvicorn --reload), frontend (vite dev)
- **Docker 服务**: db, rabbitmq
- 命令: `make dev-master`

### Worker Node  
- **本地热重载**: worker (air)
- **Docker 服务**: code-server
- 命令: `make dev-worker`

## Production Mode (生产模式)

### Master Node
- **Podman 容器**: backend, frontend, db, rabbitmq
- 命令: `make prod-master`

### Worker Node
- **Podman 容器**: worker, code-server
- 命令: `make prod-worker`

## Makefile Commands (简化后)

```makefile
# ===== 开发模式 =====
make dev-master      # 启动 master 开发环境 (db/rabbitmq Docker + 本地热重载 backend/frontend)
make dev-worker      # 启动 worker 开发环境 (code-server Docker + 本地热重载 agent)
make dev-services    # 仅启动 Docker 服务 (db + rabbitmq)
make dev-down        # 停止开发环境

# ===== 生产模式 =====
make prod-master     # 启动 master 生产环境 (Podman)
make prod-worker     # 启动 worker 生产环境 (Podman)
make prod-down       # 停止生产环境

# ===== 工具命令 =====
make init            # 初始化目录
make logs            # 查看日志
make clean           # 清理
```

## Path Considerations

### 开发环境路径 (从项目根目录执行)
```yaml
# infra/dev/docker-compose.master.yml
services:
  db:
    volumes:
      - ../../data/postgres:/var/lib/postgresql/data
```

### 生产环境路径
```yaml
# infra/prod/podman-compose.master.yml
services:
  backend:
    build:
      context: ../../backend
```

## Podman vs Docker Compose

Podman Compose 与 Docker Compose 语法基本兼容，主要区别：
1. 使用 `podman-compose` 命令替代 `docker compose`
2. 无需 Docker daemon，以 rootless 模式运行更安全
3. 可生成 Kubernetes YAML (`podman generate kube`)

## Migration Notes

1. 删除根目录的 `docker-compose.yml` 和 `docker-compose.dev.yml`
2. 将现有配置迁移到 `infra/dev/` 和 `infra/prod/`
3. 更新所有路径引用（相对于 infra/dev 或 infra/prod）
4. 更新 Makefile 命令
5. 更新 .gitignore

## Risk Assessment
- **Medium Risk**: 路径变更可能导致配置错误
- **Mitigation**: 仔细验证每个路径引用

## Success Criteria
- [ ] 开发环境可正常启动 (make dev-master, make dev-worker)
- [ ] 生产环境可正常启动 (make prod-master, make prod-worker)
- [ ] 所有路径正确解析
- [ ] Podman 配置可为 K8s 迁移做准备
