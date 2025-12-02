# Change: 导航栏节点选择器

## Status: ✅ 已完成

## Why
当前系统的计算节点管理分散在单独的节点管理页面，用户在执行任务提交、文件管理等操作时，需要频繁切换页面来选择目标节点。将节点选择器放在导航栏可以：
- **全局可见**: 用户随时知道当前操作的目标节点
- **一键切换**: 无需离开当前页面即可切换节点
- **减少混乱**: 避免任务误分配到错误节点
- **提升效率**: 简化跨节点操作流程

## What Changes

### 1. 前端导航栏
在 BasicLayout 顶部导航栏添加节点选择器：

```
[Logo] [菜单...] ─────────────────── [节点选择器 ▼] [语言切换] [用户头像]
```

- **组件位置**: 导航栏右侧，语言切换器左边
- **交互方式**: 下拉菜单，显示所有在线节点
- **显示内容**:
  - 当前选中节点名称
  - 节点状态指示器（在线/离线/繁忙）
  - "Master" 主节点标识
- **下拉菜单内容**:
  - 节点列表（名称、状态、IP）
  - 节点分组（如按位置、用途分组）
  - 快速搜索/过滤
  - "查看全部节点" 链接跳转到节点管理页

### 2. 全局状态管理
创建节点选择的全局状态：

```typescript
interface NodeContext {
  currentNode: Node | null;       // 当前选中节点
  setCurrentNode: (node) => void; // 设置当前节点
  availableNodes: Node[];         // 可用节点列表
  refreshNodes: () => void;       // 刷新节点列表
}
```

### 3. 页面集成
以下页面需要响应节点选择变化：
- **Jobs**: 提交任务到选中节点
- **Files**: 浏览选中节点的文件系统
- **Datasets**: 筛选显示选中节点的数据集
- **Dashboard**: 显示选中节点的统计信息（可选）

## Technical Design

### 组件结构

```
frontend/src/
├── components/
│   └── NodeSelector/
│       ├── index.tsx        # 节点选择器主组件
│       └── NodeDropdown.tsx # 下拉菜单内容
├── contexts/
│   └── NodeContext.tsx      # 节点全局上下文
├── hooks/
│   └── useCurrentNode.ts    # 获取当前节点的 hook
└── layouts/
    └── BasicLayout.tsx      # 集成节点选择器
```

### 状态持久化
- 使用 `localStorage` 存储用户最后选择的节点
- 页面刷新后自动恢复选择
- 节点离线时自动清除或切换到可用节点

### UI 设计

```
┌──────────────────────────────────┐
│  🖥️ GPU-Server-01  ▼             │
├──────────────────────────────────┤
│  🟢 GPU-Server-01  (主节点)       │
│     192.168.1.100                │
├──────────────────────────────────┤
│  🟢 GPU-Server-02                 │
│     192.168.1.101                │
├──────────────────────────────────┤
│  🔴 GPU-Server-03  (离线)         │
│     192.168.1.102                │
├──────────────────────────────────┤
│  ────────────────────────────    │
│  📋 查看全部节点                   │
└──────────────────────────────────┘
```

### 状态指示器
- 🟢 绿色：在线且空闲
- 🟡 黄色：在线但繁忙
- 🔴 红色：离线
- ⭐ 星标：主节点(Master)

## Impact

### 新增文件
- `frontend/src/components/NodeSelector/index.tsx`
- `frontend/src/components/NodeSelector/NodeDropdown.tsx`
- `frontend/src/contexts/NodeContext.tsx`
- `frontend/src/hooks/useCurrentNode.ts`

### 修改文件
- `frontend/src/layouts/BasicLayout.tsx` - 添加节点选择器
- `frontend/src/pages/Jobs.tsx` - 使用当前节点提交任务
- `frontend/src/pages/Files/index.tsx` - 根据节点切换文件浏览
- `frontend/src/locales/*.json` - 添加国际化文本

### 后端（可选）
- 如果需要支持"节点分组"功能，可能需要扩展节点 API

## Implementation Order

1. [x] 创建 `NodeContext` 全局状态
2. [x] 创建 `NodeSelector` 组件
3. [x] 集成到 `BasicLayout` 导航栏
4. [x] 添加 `localStorage` 持久化
5. [ ] 更新 Jobs 页面使用当前节点（未来增强）
6. [ ] 更新 Files 页面使用当前节点（未来增强）
7. [x] 添加 i18n 翻译
8. [ ] 添加节点状态实时更新（未来可选 WebSocket）

## UX Considerations

1. **默认选择**: 首次访问默认选择 Master 节点
2. **节点离线处理**: 当前节点离线时提示用户切换
3. **键盘导航**: 支持键盘快捷键快速切换节点
4. **响应式设计**: 移动端显示精简版本
