## 1. Makefile
- [x] 1.1 创建 Makefile 包含开发/生产环境命令
- [x] 1.2 添加日志查看命令
- [x] 1.3 添加代理构建支持

## 2. Development Docker Compose
- [x] 2.1 创建 `docker-compose.dev.yml` 开发环境配置
- [x] 2.2 配置后端热重载（挂载源码 + --reload）
- [x] 2.3 配置前端 Vite 开发模式
- [x] 2.4 添加构建代理参数支持（network: host + build args）

## 3. Environment Files
- [x] 3.1 创建 `.env.dev` 开发环境变量
- [x] 3.2 确认 `.gitignore` 正确配置

## 4. Dockerfiles
- [x] 4.1 创建 `backend/Dockerfile.dev` 开发用镜像
- [x] 4.2 创建 `frontend/Dockerfile.dev` 开发用镜像
- [x] 4.3 添加阿里云 apt 镜像源
- [x] 4.4 添加代理 ARG 支持

## 5. Testing
- [x] 5.1 测试 `make dev-up` 启动开发环境
- [x] 5.2 测试日志查看命令
