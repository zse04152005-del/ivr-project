# 老年人体检预约 IVR 自动外呼系统

自动批量拨打老年人电话，通过语音按键完成体检预约登记，配套 Web 管理后台。

```
用户接通
  → 播放开场白
  → 按 1（愿意体检）→ 按 1 转人工预约 / 按 2 下次再约
  → 按 2（不愿意）  → 礼貌结束
  → 无响应          → 重复提示，仍无响应则挂机，自动重拨最多 3 次
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 · FastAPI · SQLAlchemy |
| 数据库 | SQLite（开发）/ MySQL（生产）|
| 前端 | React 18 · Vite · Ant Design 5 |
| 外呼平台 | 阿里云语音服务（生产）/ Mock 模拟（测试）|

---

## 项目结构

```
ivr-project/
├── backend/
│   ├── main.py                        # FastAPI 入口
│   ├── config.py                      # 全局配置
│   ├── models.py                      # 数据库模型
│   ├── schemas.py                     # Pydantic 数据结构
│   ├── database.py                    # DB 连接 / 初始化
│   ├── requirements.txt
│   ├── .env.example                   # 配置模板
│   ├── routers/
│   │   ├── patients.py                # 老人信息管理
│   │   ├── tasks.py                   # 拨打任务管理
│   │   ├── appointments.py            # 预约管理
│   │   ├── callbacks.py               # 阿里云状态回调
│   │   ├── stats.py                   # 统计报表 & Excel 导出
│   │   └── twilio_webhook.py          # Twilio IVR 回调（备用）
│   ├── services/
│   │   ├── call_engine.py             # 外呼核心引擎
│   │   └── cloud_adapters/
│   │       ├── aliyun.py              # 阿里云适配器（生产）
│   │       ├── twilio_adapter.py      # Twilio 适配器（备用）
│   │       └── mock_adapter.py        # Mock 模拟适配器（测试）
│   └── utils/
│       └── excel_parser.py            # Excel 导入解析
└── frontend/
    ├── src/
    │   ├── main.jsx                   # 入口（dayjs 插件注册）
    │   ├── App.jsx                    # 路由 & 全局配置
    │   ├── api/index.js               # Axios 请求封装
    │   ├── layouts/MainLayout.jsx     # 侧边栏 + 弹屏轮询
    │   └── pages/
    │       ├── PatientList.jsx        # 号码管理（Excel 导入）
    │       ├── TaskCreate.jsx         # 发起外呼任务
    │       ├── TaskMonitor.jsx        # 实时监控 & 暂停/恢复
    │       ├── Report.jsx             # 结果报表 & Excel 导出
    │       └── Appointment.jsx        # 预约管理 & 转接弹屏
    └── package.json
```

---

## 快速启动（本地开发）

### 1. 环境准备

```bash
# 需要 Python 3.12（pydantic 2.x 不支持 3.13）
conda create -n ivr python=3.12 -y
conda activate ivr
```

### 2. 后端

```bash
cd backend
pip install -r requirements.txt

# 复制配置模板
cp .env.example .env
# 编辑 .env，至少设置 CALL_PLATFORM（见下方说明）

python main.py
# 服务启动在 http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

---

## 云通信平台配置

系统支持三种模式，通过 `.env` 中的 `CALL_PLATFORM` 切换，**无需修改任何代码**。

### 模式一：Mock 模拟（无需账号，立即可用）

用于本地功能测试，系统会模拟真实呼叫并随机生成按键结果。

```env
CALL_PLATFORM=mock
```

模拟结果概率：转人工 40% · 下次再约 25% · 拒绝 15% · 无人接听 20%

---

### 模式二：阿里云语音服务（生产推荐）

**前提条件：**
- 阿里云企业账号（需营业执照）
- 开通「语音服务」并完成资质审核（3~7 工作日）
- 申请外显号码
- 上传语音文件（开场白 WAV/MP3），获取 VoiceCode

**配置步骤：**

1. 登录 [阿里云控制台](https://console.aliyun.com) → 搜索「语音服务」
2. 创建 AccessKey：右上角头像 → AccessKey 管理
3. 上传语音文件：语音服务控制台 → 语音文件管理 → 获取 VoiceCode
4. 在 `.env` 中填入：

```env
CALL_PLATFORM=aliyun
PUBLIC_URL=https://your-server-domain.com    # 服务器公网地址（接收回调）

ALIYUN_ACCESS_KEY=your_access_key_id
ALIYUN_ACCESS_SECRET=your_access_key_secret
ALIYUN_CALLER_NUMBER=0571xxxxxxxx            # 申请的外显号码
ALIYUN_VOICE_CODE_OPENING=xxxxxxxx          # 语音文件 VoiceCode

AGENT_PHONE_NUMBER=138xxxxxxxx              # 人工客服接听号码
```

5. 安装阿里云 SDK：

```bash
pip install alibabacloud-dyvmsapi20170525
```

> **回调地址配置：** 阿里云需要能访问到你的服务器，`PUBLIC_URL` 必须是公网可达的 HTTPS 地址。生产部署后填服务器域名即可。

---

### 模式三：Twilio（备用方案）

个人账号可用，适合无法立即获取企业资质时测试真实外呼。

**配置步骤：**

1. 注册 [Twilio](https://twilio.com)，获取 Account SID 和 Auth Token
2. 购买一个支持中国的号码（约 $1/月）
3. 在本地使用 [ngrok](https://ngrok.com) 暴露服务（接收 Twilio 回调）：

```bash
ngrok http 8000
# 复制生成的 https://xxxx.ngrok-free.app 地址
```

4. 在 `.env` 中填入：

```env
CALL_PLATFORM=twilio
PUBLIC_URL=https://xxxx.ngrok-free.app       # ngrok 地址

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_CALLER_NUMBER=+1xxxxxxxxxx            # Twilio 购买的号码

AGENT_PHONE_NUMBER=+86138xxxxxxxx           # 转接目标（含国家码）
```

---

## 环境变量完整说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./ivr_system.db` |
| `CALL_PLATFORM` | 外呼平台：`aliyun` / `twilio` / `mock` | `aliyun` |
| `PUBLIC_URL` | 服务器公网地址（回调用） | 空 |
| `ALIYUN_ACCESS_KEY` | 阿里云 AccessKey ID | 空 |
| `ALIYUN_ACCESS_SECRET` | 阿里云 AccessKey Secret | 空 |
| `ALIYUN_CALLER_NUMBER` | 阿里云外显号码 | 空 |
| `ALIYUN_VOICE_CODE_OPENING` | 开场白语音文件 VoiceCode | 空 |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | 空 |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | 空 |
| `TWILIO_CALLER_NUMBER` | Twilio 主叫号码 | 空 |
| `AGENT_PHONE_NUMBER` | 人工客服接听号码（转接目标）| 空 |

---

## IVR 流程说明

```
发起批次
  └─► call_engine.py 取 pending 任务
        └─► 调用适配器 initiate_call()
              ├─► [阿里云] 回调 POST /api/callback/dtmf     ← 按键事件
              │                POST /api/callback/call-status ← 通话结束
              ├─► [Twilio]  回调 POST /api/twilio/voice/{id}  ← 接通
              │                  POST /api/twilio/dtmf/{id}/layer1/2
              │                  POST /api/twilio/status/{id}
              └─► [Mock]    后台线程直接更新 DB（3~8 秒延迟）

按键结果 → DB 状态更新
  transferred  → 前端弹屏（每 6 秒轮询 /api/tasks/pending-transfers）
  to_schedule  → 记录待约，下次跟进
  rejected     → 记录拒绝
  no_answer    → 自动重拨（最多 MAX_RETRY=3 次）
```

---

## 生产部署（概要）

```bash
# 1. 服务器安装 Python 3.12 + Node.js
# 2. 构建前端静态文件
cd frontend && npm run build

# 3. 后端用 gunicorn / uvicorn 生产模式启动
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 4. Nginx 反向代理前端静态文件 + 后端 API
# 5. .env 中将 DATABASE_URL 换为 MySQL，CALL_PLATFORM=aliyun
```
