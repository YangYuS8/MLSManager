## ADDED Requirements

### Requirement: Centralized Environment Configuration
系统 SHALL 使用集中的环境配置文件管理所有服务的环境变量。

#### Scenario: Development environment configuration
- **WHEN** 开发者启动开发环境（本地或 Docker）
- **THEN** 所有环境变量应从 `.env.dev` 文件加载

#### Scenario: Production environment configuration
- **WHEN** 部署生产环境
- **THEN** 所有环境变量应从 `.env` 文件加载

#### Scenario: Environment variable hierarchy
- **WHEN** 环境变量在多处定义
- **THEN** 优先级为：运行时参数 > env_file > Dockerfile 默认值

### Requirement: Environment File Structure
环境配置文件 SHALL 包含以下分类的配置项：

#### Scenario: Database configuration
- **WHEN** 配置数据库连接
- **THEN** 应包含 `POSTGRES_*` 和 `DATABASE_URL` 变量

#### Scenario: Message queue configuration
- **WHEN** 配置消息队列
- **THEN** 应包含 `RABBITMQ_*` 变量

#### Scenario: Application configuration
- **WHEN** 配置应用程序
- **THEN** 应包含 `SECRET_KEY`, `DEBUG`, `ENVIRONMENT`, `CORS_ORIGINS` 等变量

#### Scenario: Worker agent configuration
- **WHEN** 配置 Worker Agent
- **THEN** 应包含 `AGENT_*` 前缀的变量

#### Scenario: Build proxy configuration
- **WHEN** 配置构建代理（中国区加速）
- **THEN** 应包含 `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` 变量
