# Change: Frontend API Integration

## Status: ✅ 已完成

## Why
当前前端使用手动的 axios 封装调用 API，缺乏类型安全。已生成的 `@hey-api/openapi-ts` 客户端提供了完整的类型定义和 API 方法，需要将现有页面迁移到使用生成的 API 客户端，以获得：
- 完整的 TypeScript 类型检查
- 自动补全和 IDE 支持
- API 变更时的编译期错误检测
- 更好的开发体验

## What Changes

### 1. API 客户端配置
- 配置 `@hey-api/client-fetch` 客户端，添加认证拦截器
- 创建 `src/api/client.ts` 统一配置

### 2. 页面迁移
- ✅ Login.tsx - 使用生成的登录 API
- ✅ Dashboard.tsx - 使用节点/数据集/任务统计 API
- ✅ Nodes.tsx - 完整的节点 CRUD + 统计
- ✅ Datasets.tsx - 完整的数据集 CRUD + 搜索
- ✅ Jobs.tsx - 完整的任务 CRUD + 日志查看 + 提交表单
- ✅ Users.tsx - 用户管理

### 3. 新增功能
- 任务提交表单（Modal）
- 任务日志查看器
- 节点详情页（资源监控）
- 数据集搜索功能

## 实现文件

### 新增文件
- `src/api/client.ts` - API 客户端配置

### 修改文件
- `src/pages/Login.tsx` - 使用生成的 API
- `src/pages/Dashboard.tsx` - 使用生成的 API
- `src/pages/Nodes.tsx` - 使用生成的 API + 添加功能
- `src/pages/Datasets.tsx` - 使用生成的 API + 添加搜索
- `src/pages/Jobs.tsx` - 使用生成的 API + 任务提交 + 日志
- `src/pages/Users.tsx` - 使用生成的 API

## Impact
- 提升代码类型安全性
- 减少运行时错误
- 改善开发体验
- 为后续功能开发奠定基础
