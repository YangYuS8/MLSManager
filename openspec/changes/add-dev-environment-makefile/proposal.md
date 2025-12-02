# Change: Add Development Environment with Makefile

## Status: ✅ 已完成

## Why
简化开发和部署流程，提供统一的命令入口：
- 开发者需要一键启动开发环境
- 需要区分开发环境和生产环境的 Docker 配置
- 便于通过 Makefile 标准化常用操作

## What Changes
- 添加 `Makefile` 统一管理常用命令
- 添加 `docker-compose.dev.yml` 开发环境配置（热重载）
- 添加 `.env.dev` 开发环境变量文件
- 重命名现有 `docker-compose.yml` 为生产环境配置

## Impact
- Affected files: 新增 `Makefile`, `docker-compose.dev.yml`, `.env.dev`
- No breaking changes
- Improves developer experience
