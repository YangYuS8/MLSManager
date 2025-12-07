# Change: Unify Environment Variable Management

## Why
当前项目的环境变量分散在多个位置（Makefile、docker-compose 文件、Dockerfile 中），导致：
- 配置难以维护，修改一个值需要在多处更新
- 开发和生产环境配置混乱，容易出错
- 不符合 DRY 原则，存在大量重复配置

## What Changes
- 将开发模式的所有环境变量统一到 `.env.dev` 文件管理
- 将生产模式的所有环境变量统一到 `.env` 文件管理
- 更新 Makefile 从环境文件加载变量
- 更新 docker-compose 文件引用 env_file
- 清理 Dockerfile 中的默认环境变量（保留运行时必需的默认值）

## Impact
- Affected specs: infrastructure (新建)
- Affected files:
  - `.env.dev` - 扩展开发环境配置
  - `.env` - 新建生产环境配置
  - `.env.example` - 更新模板说明
  - `Makefile` - 本地开发命令从 .env.dev 加载变量
  - `docker-compose.dev.yml` - 统一使用 env_file
  - `docker-compose.yml` - 使用 env_file 引用 .env
  - `worker/Dockerfile` - 移除硬编码默认值
  - `worker/Dockerfile.dev` - 移除硬编码默认值
