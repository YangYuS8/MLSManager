# ML-Server-Manager Infrastructure

本目录包含所有容器编排配置文件。

## 目录结构

```
infra/
├── dev/                    # 开发环境 (Docker Compose)
│   ├── master.yml          # Master 节点: db + rabbitmq
│   ├── worker.yml          # Worker 节点: code-server
│   ├── .env.master.example # Master 环境变量模板
│   └── .env.worker.example # Worker 环境变量模板
│
├── prod/                   # 生产环境 (Podman Compose)
│   ├── master.yml          # Master 节点: 全部服务
│   ├── worker.yml          # Worker 节点: agent + code-server
│   ├── .env.master.example
│   └── .env.worker.example
│
└── README.md               # 本文件
```

## 开发模式

开发模式下，前端和后端在本地以热重载方式运行，仅基础设施服务（数据库、消息队列）使用 Docker。

### Master 节点

```bash
# 从项目根目录执行
make dev-master
```

这会：
1. 启动 Docker 服务 (PostgreSQL, RabbitMQ)
2. 本地运行 backend (uvicorn --reload)
3. 本地运行 frontend (vite dev)

### Worker 节点

```bash
# 从项目根目录执行
make dev-worker
```

这会：
1. 启动 Docker 服务 (code-server)
2. 本地运行 worker (air 热重载)

## 生产模式

生产模式使用 Podman 运行所有服务，为后续迁移 Kubernetes 做准备。

### Master 节点

```bash
make prod-master
```

### Worker 节点

```bash
make prod-worker
```

## 环境配置

1. 复制对应的 `.env.*.example` 文件并重命名（去掉 `.example`）
2. 根据实际环境修改配置

## Podman vs Docker

- Podman 与 Docker Compose 语法基本兼容
- Podman 以 rootless 模式运行，更安全
- 可使用 `podman generate kube` 生成 Kubernetes YAML
