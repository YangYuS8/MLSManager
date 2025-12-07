# ML-Server-Manager Makefile
# 简化的开发和生产命令

.PHONY: help init \
        dev-master dev-worker dev-services dev-down \
        prod-master prod-worker prod-down \
        logs clean

# =============================================================================
# 默认目标
# =============================================================================

help:
	@echo "ML-Server-Manager 命令"
	@echo ""
	@echo "=== 初始化 ==="
	@echo "  make init             初始化数据目录 (首次运行)"
	@echo ""
	@echo "=== 开发模式 (Docker + 本地热重载) ==="
	@echo "  make dev-master       启动 Master 开发环境"
	@echo "                        (Docker: db/rabbitmq, 本地: backend/frontend)"
	@echo "  make dev-worker       启动 Worker 开发环境"
	@echo "                        (Docker: code-server, 本地: worker)"
	@echo "  make dev-services     仅启动 Docker 服务"
	@echo "  make dev-down         停止开发环境"
	@echo ""
	@echo "=== 生产模式 (Podman) ==="
	@echo "  make prod-master      启动 Master 生产环境"
	@echo "  make prod-worker      启动 Worker 生产环境"
	@echo "  make prod-down        停止生产环境"
	@echo ""
	@echo "=== 工具 ==="
	@echo "  make logs             查看日志"
	@echo "  make clean            清理容器和镜像"
	@echo ""
	@echo "配置文件: infra/dev/.env.* (开发) | infra/prod/.env.* (生产)"

# =============================================================================
# 初始化
# =============================================================================

init:
	@echo "创建数据目录..."
	mkdir -p data/postgres
	mkdir -p data/rabbitmq
	mkdir -p data/projects
	mkdir -p data/datasets
	mkdir -p data/jobs
	mkdir -p data/.ml-agent
	mkdir -p data/.code-server/config
	mkdir -p data/.code-server/data
	chmod -R 755 data
	@echo ""
	@echo "复制环境变量模板..."
	@test -f infra/dev/.env.master || cp infra/dev/.env.master.example infra/dev/.env.master
	@test -f infra/dev/.env.worker || cp infra/dev/.env.worker.example infra/dev/.env.worker
	@echo "完成! 请检查并修改 infra/dev/.env.* 中的配置"

# =============================================================================
# 开发模式
# =============================================================================

# 启动 Docker 服务 (db + rabbitmq + code-server)
dev-services-up:
	@echo "启动开发服务 (db + rabbitmq + code-server)..."
	docker compose -f infra/dev/master.yml --env-file infra/dev/.env.master up -d
	docker compose -f infra/dev/worker.yml --env-file infra/dev/.env.worker up -d

# 停止 Docker 服务
dev-services-down:
	docker compose -f infra/dev/master.yml --env-file infra/dev/.env.master down
	docker compose -f infra/dev/worker.yml --env-file infra/dev/.env.worker down
	@echo "开发服务已停止"

# 启动后端开发环境 (热重载)
dev-backend:
	@echo "启动 Backend (热重载)..."
	cd backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动前端开发环境 (热重载)
dev-frontend:
	@echo "启动 Frontend (热重载)..."
	cd frontend && pnpm dev

# 启动 Worker开发环境 (热重载)
dev-worker:
	@echo "启动 Worker (热重载)..."
	cd worker && \
	  AGENT_STORAGE_PATH="$(PWD)/data" \
	  AGENT_DATASETS_PATH="$(PWD)/data/datasets" \
	  AGENT_PROJECTS_PATH="$(PWD)/data/projects" \
	  AGENT_TOKEN_FILE="$(PWD)/data/.ml-agent/token" \
	  air

# =============================================================================
# 生产模式 (Podman)
# =============================================================================

# Master 生产环境
prod-master:
	@echo "启动 Master 生产环境 (Podman)..."
	@test -f infra/prod/.env.master || (echo "错误: 请先创建 infra/prod/.env.master" && exit 1)
	podman-compose -f infra/prod/master.yml --env-file infra/prod/.env.master up -d

# Worker 生产环境
prod-worker:
	@echo "启动 Worker 生产环境 (Podman)..."
	@test -f infra/prod/.env.worker || (echo "错误: 请先创建 infra/prod/.env.worker" && exit 1)
	podman-compose -f infra/prod/worker.yml --env-file infra/prod/.env.worker up -d

# 构建生产镜像
prod-build:
	@echo "构建生产镜像..."
	podman-compose -f infra/prod/master.yml --env-file infra/prod/.env.master build
	podman-compose -f infra/prod/worker.yml --env-file infra/prod/.env.worker build

# 停止所有生产环境
prod-down:
	-podman-compose -f infra/prod/master.yml --env-file infra/prod/.env.master down
	-podman-compose -f infra/prod/worker.yml --env-file infra/prod/.env.worker down

# =============================================================================
# 日志
# =============================================================================

logs:
	@echo "选择要查看的日志:"
	@echo "  make logs-dev-master   开发 Master 日志"
	@echo "  make logs-dev-worker   开发 Worker 日志"
	@echo "  make logs-prod-master  生产 Master 日志"
	@echo "  make logs-prod-worker  生产 Worker 日志"

logs-dev-master:
	docker compose -f infra/dev/master.yml --env-file infra/dev/.env.master logs -f

logs-dev-worker:
	docker compose -f infra/dev/worker.yml --env-file infra/dev/.env.worker logs -f

logs-prod-master:
	podman-compose -f infra/prod/master.yml --env-file infra/prod/.env.master logs -f

logs-prod-worker:
	podman-compose -f infra/prod/worker.yml --env-file infra/prod/.env.worker logs -f

# =============================================================================
# 清理
# =============================================================================

clean:
	@echo "停止并清理所有容器..."
	-docker compose -f infra/dev/master.yml --env-file infra/dev/.env.master down -v --rmi local
	-docker compose -f infra/dev/worker.yml --env-file infra/dev/.env.worker down -v --rmi local
	-podman-compose -f infra/prod/master.yml --env-file infra/prod/.env.master down -v --rmi local
	-podman-compose -f infra/prod/worker.yml --env-file infra/prod/.env.worker down -v --rmi local

clean-data:
	@echo "警告: 这将删除所有数据 (数据库, 项目, 数据集等)"
	@read -p "确定要继续吗? [y/N] " confirm && [ "$$confirm" = "y" ]
	rm -rf data/
