# Change: 项目文件管理功能

## Status: ✅ 已完成

## Why
当前系统缺少文件管理功能，用户无法直接在 Web 界面浏览和管理计算节点上的项目文件。参考 1Panel 的文件管理设计，添加类似的功能可以：
- 让用户方便地浏览节点上的数据集、模型、日志等文件
- 支持基本的文件操作（上传、下载、创建、删除、重命名等）
- 提供代码/配置文件的在线查看和编辑
- 简化用户管理 ML 项目文件的流程

## What Changes

### 1. 后端 API
新增文件管理相关的 API 端点：

- `GET /api/v1/files/list` - 列出目录内容
- `GET /api/v1/files/read` - 读取文件内容
- `POST /api/v1/files/create` - 创建文件/目录
- `POST /api/v1/files/upload` - 上传文件
- `GET /api/v1/files/download` - 下载文件
- `PUT /api/v1/files/rename` - 重命名文件/目录
- `PUT /api/v1/files/move` - 移动文件/目录
- `PUT /api/v1/files/copy` - 复制文件/目录
- `DELETE /api/v1/files/delete` - 删除文件/目录
- `GET /api/v1/files/info` - 获取文件/目录信息（权限、大小、时间等）
- `PUT /api/v1/files/permission` - 修改文件权限
- `POST /api/v1/files/compress` - 压缩文件
- `POST /api/v1/files/decompress` - 解压文件
- `POST /api/v1/files/search` - 搜索文件

### 2. 前端页面
新增文件管理页面，参考 1Panel 设计：

- **标签式多窗口**: 支持同时打开多个文件浏览标签
- **面包屑导航**: 显示当前路径，支持快速跳转
- **工具栏**:
  - 导航按钮（后退、前进、返回上级、刷新）
  - 新建文件/目录
  - 上传文件
  - 下载文件
  - 搜索
  - 显示/隐藏隐藏文件
- **文件列表**: 
  - 表格展示：名称、权限、所有者、大小、修改时间
  - 图标区分文件类型（文件夹、代码文件、图片、压缩包等）
  - 支持排序和筛选
- **右键菜单**: 
  - 打开、重命名、复制、移动、删除
  - 下载、压缩/解压
  - 查看属性、修改权限
- **文件预览/编辑**:
  - 代码文件：语法高亮编辑器（Monaco Editor）
  - 图片：预览查看
  - 文本文件：纯文本查看/编辑
- **拖拽上传**: 支持拖拽文件到界面进行上传

### 3. Worker Agent 扩展
扩展 Worker Agent 以支持文件操作：
- 文件系统操作的安全边界（限制可访问的目录）
- 大文件分片上传/下载
- 文件操作权限检查

## Technical Design

### 后端架构

```
backend/app/
├── api/v1/endpoints/
│   └── files.py          # 文件管理 API 路由
├── schemas/
│   └── files.py          # 文件相关 Pydantic 模型
├── services/
│   └── file_service.py   # 文件操作业务逻辑
└── utils/
    └── file_utils.py     # 文件操作工具函数
```

### 前端结构

```
frontend/src/
├── pages/
│   └── Files/
│       ├── index.tsx           # 文件管理主页面
│       ├── components/
│       │   ├── FileTable.tsx   # 文件列表表格
│       │   ├── Toolbar.tsx     # 工具栏
│       │   ├── Breadcrumb.tsx  # 面包屑导航
│       │   ├── UploadModal.tsx # 上传对话框
│       │   ├── CreateModal.tsx # 新建对话框
│       │   ├── MoveModal.tsx   # 移动/复制对话框
│       │   ├── PermissionModal.tsx # 权限对话框
│       │   └── FilePreview.tsx # 文件预览
│       └── hooks/
│           └── useFileManager.ts # 文件管理 hooks
├── components/
│   └── CodeEditor/
│       └── index.tsx     # Monaco 代码编辑器组件
```

### 安全考虑

1. **路径遍历防护**: 验证并规范化所有路径，防止 `../` 攻击
2. **权限控制**: 基于用户角色限制文件操作范围
3. **配额限制**: 限制上传文件大小和存储空间
4. **敏感文件保护**: 禁止访问系统关键文件

## Impact

### 新增文件
- `backend/app/api/v1/endpoints/files.py`
- `backend/app/schemas/files.py`
- `backend/app/services/file_service.py`
- `frontend/src/pages/Files/` 目录下所有文件
- `frontend/src/components/CodeEditor/`

### 修改文件
- `backend/app/api/v1/router.py` - 添加文件路由
- `frontend/src/layouts/BasicLayout.tsx` - 添加文件管理菜单
- `frontend/src/locales/*.json` - 添加国际化文本
- `worker_agent/` - 扩展文件操作支持

### 依赖
- 前端: `@monaco-editor/react` (代码编辑器)

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| 路径遍历攻击 | 严格校验路径，使用白名单目录 |
| 大文件上传阻塞 | 分片上传，进度显示 |
| 敏感信息泄露 | RBAC 权限控制，审计日志 |
| 存储空间耗尽 | 配额管理，定期清理 |

## 实现阶段

### Phase 1: 基础功能（MVP）
- [x] 目录浏览和文件列表
- [x] 文件/目录创建和删除
- [x] 文件上传和下载
- [x] 基本重命名功能

### Phase 2: 增强功能
- [x] 文件搜索
- [x] 移动和复制
- [x] 权限管理
- [x] 压缩和解压

### Phase 3: 高级功能
- [x] 代码编辑器集成（使用 textarea，未来可升级 Monaco）
- [ ] 多标签窗口（未来增强）
- [x] 拖拽上传
- [x] 文件预览（文本、图片）
