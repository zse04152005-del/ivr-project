# 开发任务清单

> 按顺序完成，每个任务完成后打勾 ✅

---

## 阶段一：环境搭建 & 数据库（第1天）

- [ ] **T1.1** 初始化 backend 项目，安装依赖（FastAPI, SQLAlchemy, openpyxl, uvicorn）
- [ ] **T1.2** 编写 config.py 配置文件（数据库连接、云通信密钥占位、外呼时间段等）
- [ ] **T1.3** 编写 database.py 数据库连接
- [ ] **T1.4** 编写 models.py 三张表模型
  - patients（id, name, phone, age, community, created_at）
  - call_tasks（id, batch_id, patient_id, status, call_count, called_at, key_pressed, transferred, notes）
  - appointments（id, patient_id, task_id, appointment_date, appointment_time, operator, created_at）
- [ ] **T1.5** 运行数据库迁移，确认表创建成功
- [ ] **T1.6** 编写 schemas.py 请求/响应模型

---

## 阶段二：老人信息管理 API（第2天）

- [ ] **T2.1** 编写 Excel 导入解析工具（utils/excel_parser.py）
  - 支持 .xlsx 和 .csv
  - 解析姓名、电话、年龄、社区字段
  - 数据校验（电话格式、年龄范围）
  - 返回成功/失败条数
- [ ] **T2.2** 编写 patients 路由（routers/patients.py）
  - POST /api/patients/import — 上传Excel批量导入
  - GET /api/patients — 分页查询列表（支持按姓名/社区搜索）
  - GET /api/patients/{id} — 查询单个
  - PUT /api/patients/{id} — 编辑
  - DELETE /api/patients/{id} — 删除
  - GET /api/patients/count — 统计总数
- [ ] **T2.3** 用 Postman/curl 测试所有接口

---

## 阶段三：拨打任务 API（第3-4天）

- [ ] **T3.1** 编写任务管理路由（routers/tasks.py）
  - POST /api/tasks/create — 创建批次任务
    - 入参：选择的患者ID列表 或 社区筛选条件
    - 自动生成 batch_id
    - 为每个患者创建一条 call_task 记录（status=pending）
  - GET /api/tasks/batches — 查询所有批次
  - GET /api/tasks/batch/{batch_id} — 查询某批次详情
  - POST /api/tasks/batch/{batch_id}/start — 启动拨打
  - POST /api/tasks/batch/{batch_id}/pause — 暂停
  - GET /api/tasks/batch/{batch_id}/stats — 统计（接通/未接/同意/拒绝/待约）
- [ ] **T3.2** 编写外呼引擎核心逻辑（services/call_engine.py）
  - 从任务队列取 pending 记录
  - 调用云通信 API 发起呼叫
  - 控制并发数量（如同时最多5路）
  - 未接通时标记并安排重拨（间隔2小时，最多3次）
  - 拨打时间限制（8:00-11:30, 14:00-17:30）
- [ ] **T3.3** 编写 IVR 流程控制（services/ivr_flow.py）
  - 呼叫接通 → 播放开场语音
  - 等待 DTMF 按键（超时15-20秒）
  - 按1 → 播放第二段语音 → 等待按键
    - 按1 → 标记 transferred=true，转接人工
    - 按2 → 标记 status=to_schedule，播放结束语，挂机
  - 按2 → 标记 status=rejected，播放结束语，挂机
  - 无按键 → 重复一次 → 仍无 → 标记 status=no_answer，挂机
  - 所有结果写入 call_tasks 表
- [ ] **T3.4** 编写云通信平台对接适配器（先写接口，具体实现根据选择的平台）
  - make_call(phone, voice_file) — 发起呼叫
  - play_voice(call_id, voice_file) — 播放语音
  - detect_dtmf(call_id, timeout) — 检测按键
  - transfer_call(call_id, agent_number) — 转接人工
  - hangup(call_id) — 挂断
- [ ] **T3.5** 编写回调接口（云通信平台通过 webhook 回调通知状态）
  - POST /api/callback/call-status — 呼叫状态回调
  - POST /api/callback/dtmf — 按键事件回调

---

## 阶段四：预约管理 API（第5天）

- [ ] **T4.1** 编写预约管理路由（routers/appointments.py）
  - POST /api/appointments — 人工客服创建预约
  - GET /api/appointments — 查询预约列表（按日期筛选）
  - PUT /api/appointments/{id} — 修改预约
  - DELETE /api/appointments/{id} — 取消预约
  - GET /api/appointments/date/{date} — 查询某天预约情况
- [ ] **T4.2** 编写报表统计接口
  - GET /api/stats/overview — 总览（总人数、已拨、接通率、同意率等）
  - GET /api/stats/batch/{batch_id} — 单批次统计
  - GET /api/stats/export/{batch_id} — 导出Excel报表

---

## 阶段五：前端管理后台（第6-8天）

- [ ] **T5.1** 初始化 React 项目（Vite + React + Ant Design）
- [ ] **T5.2** 编写布局框架（侧边栏导航 + 主内容区）
- [ ] **T5.3** 号码管理页面（PatientList.jsx）
  - Excel上传导入
  - 列表展示（分页、搜索）
  - 编辑、删除
- [ ] **T5.4** 发起任务页面（TaskCreate.jsx）
  - 选择拨打范围（全部/按社区/手动勾选）
  - 设置拨打时间段、并发数
  - 一键开始
- [ ] **T5.5** 实时监控页面（TaskMonitor.jsx）
  - 当前批次进度条
  - 实时数据：已拨/接通/按1/按2/未响应
  - 暂停/继续按钮
- [ ] **T5.6** 结果报表页面（Report.jsx）
  - 饼图：同意/拒绝/未接/待约 占比
  - 列表：每通电话详情
  - 导出Excel按钮
- [ ] **T5.7** 预约管理页面（Appointment.jsx）
  - 日历视图查看每天预约数
  - 人工录入预约时间
  - 待约列表（转人工后需要跟进的）
- [ ] **T5.8** 人工客服弹屏功能
  - 转接电话时，页面自动弹出该老人信息
  - 客服可直接填写预约时间并提交

---

## 阶段六：语音文件准备（与开发并行）

- [ ] **T6.1** 编写语音播报文案
  - 开场白：「您好XX大爷/大妈，这里是XX社区健康服务中心。您的年度免费体检到了，下周可以安排。请问您下周能来体检吗？能来请按1，不能来请按2。」
  - 预约引导：「好的，帮您登记。如果您现在就想预约具体时间，我转接人工服务，请按1。如果您等下次通知再约时间，请按2。」
  - 转人工：「正在为您转接，请稍等。」
  - 拒绝结束：「好的，祝您身体健康，再见！」
  - 待约结束：「已登记，我们会再联系您安排时间，祝您健康，再见！」
  - 无响应提示：「没有听到您的选择，请在电话上按数字1或2。」
- [ ] **T6.2** 录制语音文件（找声音温和的人录，语速慢，音量大）
- [ ] **T6.3** 音频格式转换（通常需要 8kHz, 16bit, mono, wav/mp3）

---

## 阶段七：联调测试（第9-10天）

- [ ] **T7.1** 注册云通信平台账号，开通外呼服务
- [ ] **T7.2** 完成 call_engine.py 中的平台对接代码
- [ ] **T7.3** 上传语音文件到云通信平台
- [ ] **T7.4** 用自己手机号测试完整流程
  - 测试按1-1（转人工）
  - 测试按1-2（待约）
  - 测试按2（拒绝）
  - 测试不按键（超时）
  - 测试忙音/无人接听
- [ ] **T7.5** 找10-20位老人小范围测试
- [ ] **T7.6** 根据反馈调整：语音内容、等待时间、音量等
- [ ] **T7.7** 压力测试：模拟50+并发呼叫

---

## 阶段八：上线运行（第11天起）

- [ ] **T8.1** 部署到正式服务器
- [ ] **T8.2** 导入全部老人号码
- [ ] **T8.3** 先小批量（50人）试运行
- [ ] **T8.4** 确认无问题后扩大范围
- [ ] **T8.5** 安排人工客服值班接听转接电话
- [ ] **T8.6** 每日查看报表，跟进未接通号码

---

## 关键配置项（config.py）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| CALL_START_HOUR | 8 | 最早拨打时间 |
| CALL_END_HOUR | 18 | 最晚拨打时间 |
| LUNCH_START | 12:00 | 午休开始（不拨打） |
| LUNCH_END | 14:00 | 午休结束 |
| DTMF_TIMEOUT | 18 | 按键等待秒数 |
| MAX_RETRY | 3 | 最大重拨次数 |
| RETRY_INTERVAL | 7200 | 重拨间隔（秒） |
| MAX_CONCURRENT | 5 | 最大并发呼叫数 |
| REPEAT_PROMPT | 2 | 无响应时重复次数 |
