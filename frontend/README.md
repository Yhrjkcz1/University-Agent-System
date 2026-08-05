# 赛智通前端

赛智通生产前端基于 React、TypeScript、Vite 和 Ant Design，提供首页、AI 推荐对话、竞赛库、我的竞赛、账户登录和管理员页面。

## 页面与能力

- 首页：产品入口、能力介绍和快捷导航
- AI 推荐：连续对话、画像补全、推荐卡片、详情追问和材料下载
- 竞赛库：分页读取 Supabase 中的结构化竞赛数据
- 我的竞赛：登录用户收藏管理
- 登录页：注册、登录及会话恢复
- 管理后台：用户、会话、登录日志和刷新任务管理

## 本地运行

后端先在仓库根目录启动：

```powershell
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

然后在本目录执行：

```powershell
npm install
$env:VITE_API_BASE_URL="http://localhost:8000"
npm run dev
```

访问 `http://localhost:5173`。

也可以创建 `frontend/.env.local`：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 构建验证

```powershell
npm run build
npm run preview
```

构建产物位于 `frontend/dist/`。2026-08-05 本地生产构建已通过；主 JavaScript 包约 1.23 MB，后续可通过路由懒加载和代码拆分优化首屏体积。

## API 与鉴权

- API 基址由 `VITE_API_BASE_URL` 注入。
- 未配置时，当前代码回退到 Render 生产 API。
- Access Token 通过 `Authorization: Bearer ...` 发送。
- 收到 401 后，前端尝试使用 Refresh Token 获取新 Access Token。
- Supabase service-role key、DeepSeek Key、JWT 密钥和 GitHub Token绝不能放入前端变量。

## 部署

`.github/workflows/deploy.yml` 在 `main` 更新后自动：

1. 安装 Node.js 20；
2. 执行 `npm install`；
3. 注入 `VITE_API_BASE_URL`；
4. 执行生产构建；
5. 部署 `dist/` 到 GitHub Pages。

Render 后端的 `ALLOWED_ORIGINS` 必须包含实际 GitHub Pages Origin，否则浏览器会因 CORS 拒绝请求。

## 验收重点

1. 未登录用户可浏览首页和公开竞赛。
2. 注册、登录、刷新令牌和退出正常。
3. 对话刷新页面后可按产品设计恢复。
4. 推荐卡片、详情链接和 Word 下载可用。
5. 收藏与“我的竞赛”保持一致。
6. 管理员和普通用户页面权限隔离。
7. 后端不可用时展示用户可理解的错误，不泄露内部异常。

更多信息见仓库根目录 [README](../README.md) 和 [验收指南](../docs/ACCEPTANCE_GUIDE_CN.md)。
