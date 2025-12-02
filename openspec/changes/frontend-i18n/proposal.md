# Change: Frontend i18n 国际化支持

## Status: ✅ 已完成

## Why
当前前端界面只有英文，需要添加国际化支持以便：
- 支持中文用户使用
- 遵循系统语言偏好自动切换
- 提供语言切换功能

## What Changes

### 1. i18n 基础设施
- 使用 `react-i18next` + `i18next` 实现国际化
- 使用 `i18next-browser-languagedetector` 检测系统语言
- 创建语言资源文件 (zh-CN, en-US)

### 2. 语言资源
- 通用文本：导航、按钮、表单标签
- 页面特定文本：各页面标题、表格列名、提示信息
- 错误消息

### 3. UI 组件
- 语言切换器组件
- 集成到布局头部

## 实现文件

### 新增文件
- `src/locales/zh-CN.json` - 简体中文翻译
- `src/locales/en-US.json` - 英文翻译
- `src/locales/index.ts` - i18n 配置
- `src/components/LanguageSwitcher.tsx` - 语言切换组件

### 修改文件
- `src/main.tsx` - 引入 i18n
- `src/layouts/BasicLayout.tsx` - 添加语言切换器
- 所有页面文件 - 使用 `useTranslation` hook

## Impact
- 支持简体中文和英文
- 自动检测系统语言
- 用户可手动切换语言
