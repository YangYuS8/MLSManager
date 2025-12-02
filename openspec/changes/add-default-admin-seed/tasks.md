## 1. Backend Configuration
- [x] 1.1 添加默认管理员配置到 `app/core/config.py`
- [x] 1.2 更新 `.env.example` 添加默认管理员凭据

## 2. Database Seeding
- [x] 2.1 创建 `app/core/seed.py` 实现用户种子逻辑
- [x] 2.2 在 `main.py` 的 lifespan 中调用种子函数

## 3. Bug Fix
- [x] 3.1 替换 `passlib` 为直接使用 `bcrypt`（解决兼容性问题）

## 4. Testing
- [x] 4.1 验证后端启动时自动创建管理员
- [x] 4.2 验证可以使用默认凭据登录
