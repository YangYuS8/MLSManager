## 1. 创建和更新环境配置文件
- [x] 1.1 扩展 `.env.dev`，添加所有开发环境变量（数据库、RabbitMQ、代理、Worker 等）
- [x] 1.2 创建 `.env`，定义所有生产环境变量
- [x] 1.3 更新 `.env.example`，作为完整的配置模板文档

## 2. 更新 Docker Compose 配置
- [x] 2.1 更新 `docker-compose.dev.yml`，所有服务统一使用 `env_file: .env.dev`
- [x] 2.2 更新 `docker-compose.yml`，所有服务使用 `env_file: .env`
- [x] 2.3 移除 docker-compose 中的硬编码环境变量，改用变量引用

## 3. 更新 Dockerfile
- [x] 3.1 清理 `worker/Dockerfile` 中的默认环境变量
- [x] 3.2 清理 `worker/Dockerfile.dev` 中的默认环境变量

## 4. 更新 Makefile
- [x] 4.1 本地开发命令从 `.env.dev` 加载环境变量
- [x] 4.2 添加 `include .env.dev` 和 `export` 逻辑

## 5. 更新 .gitignore
- [x] 5.1 确保 `.env` 在 gitignore 中（生产密钥不应提交）
- [x] 5.2 `.env.dev` 可提交（仅包含开发默认值）

## 6. 验证
- [x] 6.1 验证 `docker compose -f docker-compose.dev.yml config` 正常
- [x] 6.2 验证 `docker compose -f docker-compose.yml config` 正常
- [ ] 6.3 验证 `make services-up && make local-backend` 正常工作（需实际运行）
- [ ] 6.4 验证 `make dev` Docker 开发模式正常工作（需实际运行）
- [ ] 6.5 验证 `make prod` 生产模式正常工作（需实际运行）
