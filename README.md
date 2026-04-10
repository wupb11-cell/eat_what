# EatWhat - 每日饮食推荐助手

基于营养学原理（低GI），为中国用户推荐每日饮食搭配及详细做法的小程序后端API。

## 功能特点

- ✅ **低GI健康饮食** - 所有推荐均符合低升糖指数标准
- ✅ **中国口味** - 50+道家常中式菜谱
- ✅ **简单易做** - 难度控制在3星以内
- ✅ **成本可控** - 每餐平均成本10-30元
- ✅ **个性化设置** - 支持忌口、偏好设置
- ✅ **营养分析** - 每日营养摄入追踪
- ✅ **微信小程序** - 支持订阅消息推送

## 技术栈

- Python Flask
- SQLite 数据库
- 微信小程序 API
- Railway 部署

## 快速部署到 Railway

### 1. 上传代码到 GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/wupb11-cell/eat_what.git
git push -u origin master
```

### 2. 部署到 Railway

1. 访问 [Railway.app](https://railway.app)
2. 使用 GitHub 登录
3. 点击 "New Project" → "Deploy from GitHub"
4. 选择 `eat_what` 仓库
5. Railway 会自动部署

### 3. 配置环境变量

在 Railway 项目设置中添加：

```
WECHAT_APPID=wxd62492c53c19438c
WECHAT_APPSECRET=你的AppSecret
```

## API 接口列表

### 认证相关
- `POST /api/login` - 小程序登录
- `GET /api/user/profile` - 获取用户信息
- `POST /api/user/settings` - 更新设置
- `POST /api/user/preferences` - 更新偏好
- `POST /api/user/subscribe` - 订阅消息设置

### 菜谱相关
- `GET /api/weekly_menu` - 获取本周菜谱
- `GET /api/today_menu` - 获取今日菜谱
- `GET /api/recipe/<id>` - 获取菜谱详情
- `GET /api/recipes` - 获取菜谱列表

### 营养分析
- `GET /api/nutrition_analysis` - 获取本周营养分析
- `GET /api/nutrition_today` - 获取今日营养摄入

### 采购相关
- `GET /api/purchase_list` - 获取采购清单

## 目录结构

```
eat_what/
├── app.py              # Flask 主应用
├── database.py         # 数据库初始化
├── recommender.py      # 推荐算法
├── requirements.txt    # Python 依赖
├── Procfile           # Railway 部署配置
├── railway.json       # Railway 配置
└── .gitignore         # Git 忽略文件
```

## 本地运行

```bash
pip install -r requirements.txt
python app.py
```

## 许可证

MIT License
