# Change Proposal: Fix Database Schema and Clean Up

## Summary
1. 修复数据库缺失 `code_server_port` 列的问题
2. 清理项目根目录下不再使用的环境变量文件

## Problem Analysis

### 错误原因
```
sqlite3.OperationalError: no such column: nodes.code_server_port
```

Node 模型新增了 `code_server_port` 字段，但现有 SQLite 数据库没有这个列。
SQLAlchemy 的 `create_all()` 只会创建不存在的表，不会修改现有表结构。

### 解决方案
1. **开发环境**: 删除 SQLite 数据库文件，让系统重新创建
2. **生产环境**: 需要数据库迁移 (Alembic)

## Files to Clean Up

根目录下的旧环境文件：
- `.env.dev` - 已废弃，配置已迁移到 `infra/dev/.env.*`
- `.env` - 生产环境，配置已迁移到 `infra/prod/.env.*`
- `.env.example` - 旧模板

## Implementation

1. 删除旧的 SQLite 数据库文件
2. 清理根目录环境变量文件
3. 更新 .gitignore
