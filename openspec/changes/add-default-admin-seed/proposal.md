# Change: Add Default Admin User Seeding

## Status: ✅ 已完成

## Why
开发环境首次启动时数据库为空，无法登录系统。需要在应用启动时自动创建默认管理员账户，方便开发和测试。

## What Changes
- 在后端启动时检查并创建默认超级管理员用户
- 从环境变量读取默认管理员凭据
- 更新 `.env.example` 添加默认管理员配置

## Impact
- Affected files: `backend/main.py`, `backend/app/core/config.py`, `.env.example`
- Development experience improvement
- No breaking changes
