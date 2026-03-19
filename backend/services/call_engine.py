"""
电话外呼核心引擎（Twilio / 阿里云 双适配）

Twilio 是 webhook 驱动的：
  引擎 → 发起呼叫 → Twilio 回调 /api/twilio/voice → IVR 流程 → DB 状态更新
  引擎只负责发起呼叫，然后轮询 DB 等待结果，不阻塞串行。

阿里云同理，通过 /api/callback/* 回调更新 DB。

并发控制：最多同时 MAX_CONCURRENT 路处于 calling 状态，
          引擎在空出槽位时补入新任务。
"""
import logging
import time
from datetime import datetime, timedelta

import config

logger = logging.getLogger(__name__)

# 全局暂停标志（按批次）
_paused_batches: set = set()


def pause_calling(batch_id: str):
    """暂停某批次"""
    _paused_batches.add(batch_id)
    logger.info(f"批次 {batch_id} 已暂停")


def resume_calling(batch_id: str):
    """恢复某批次"""
    _paused_batches.discard(batch_id)
    logger.info(f"批次 {batch_id} 已恢复")


def is_callable_time() -> bool:
    """判断当前时间是否在可拨打时段内"""
    now = datetime.now()
    hour = now.hour
    time_str = f"{hour:02d}:{now.minute:02d}"
    if hour < config.CALL_START_HOUR or hour >= config.CALL_END_HOUR:
        return False
    if config.LUNCH_START <= time_str < config.LUNCH_END:
        return False
    return True


def _get_adapter():
    """根据 CALL_PLATFORM 返回对应的云通信适配器模块"""
    platform = getattr(config, "CALL_PLATFORM", "mock").lower()
    if platform == "aliyun":
        from services.cloud_adapters import aliyun as adapter
    elif platform == "twilio":
        from services.cloud_adapters import twilio_adapter as adapter
    else:
        from services.cloud_adapters import mock_adapter as adapter
    logger.info(f"使用云通信适配器: {platform}")
    return adapter


def _handle_no_answer_retries(db, batch_id: str):
    """将未接通但未超过重试次数的任务重置为 pending"""
    from models import CallTask, CallStatus

    no_answer_tasks = (
        db.query(CallTask)
        .filter(
            CallTask.batch_id == batch_id,
            CallTask.status == CallStatus.no_answer,
            CallTask.call_count < config.MAX_RETRY,
        )
        .all()
    )
    for task in no_answer_tasks:
        task.status = CallStatus.pending
        task.notes = f"第{task.call_count}次未接通，待重拨"
    if no_answer_tasks:
        db.commit()
        logger.info(f"批次 {batch_id} 重置 {len(no_answer_tasks)} 条任务待重拨")


def _handle_stale_calling(db, batch_id: str):
    """将超时停留在 calling 状态的任务标记为失败或重置"""
    from models import CallTask, CallStatus

    cutoff = datetime.now() - timedelta(seconds=180)  # 3 分钟超时
    stale = (
        db.query(CallTask)
        .filter(
            CallTask.batch_id == batch_id,
            CallTask.status == CallStatus.calling,
            CallTask.called_at < cutoff,
        )
        .all()
    )
    for task in stale:
        if task.call_count < config.MAX_RETRY:
            task.status = CallStatus.pending
            task.notes = f"第{task.call_count}次回调超时，待重拨"
        else:
            task.status = CallStatus.failed
            task.notes = "回调超时，超过最大重试次数"
    if stale:
        db.commit()
        logger.warning(f"批次 {batch_id} 处理 {len(stale)} 条超时任务")


def start_calling(batch_id: str):
    """
    启动批次拨打（在后台线程中运行）

    流程：
    1. 检查暂停 / 拨打时段
    2. 统计当前 calling 数量，计算空闲槽位
    3. 取 pending 任务填满槽位，逐个调用适配器发起呼叫
    4. 每轮 sleep 后检查超时任务和待重拨任务
    5. 所有任务进入终态后退出
    """
    from database import SessionLocal
    from models import CallTask, CallStatus

    logger.info(f"===== 开始批次拨打: {batch_id} =====")
    adapter = _get_adapter()

    while True:
        # ── 1. 暂停检查 ────────────────────────────────────────
        if batch_id in _paused_batches:
            logger.info(f"批次 {batch_id} 已暂停，等待恢复...")
            time.sleep(5)
            continue

        # ── 2. 时段检查 ────────────────────────────────────────
        if not is_callable_time():
            logger.info("当前不在拨打时段，等待...")
            time.sleep(60)
            continue

        db = SessionLocal()
        try:
            # ── 3. 计算空闲槽位 ────────────────────────────────
            calling_count = (
                db.query(CallTask)
                .filter(
                    CallTask.batch_id == batch_id,
                    CallTask.status == CallStatus.calling,
                )
                .count()
            )
            slots = config.MAX_CONCURRENT - calling_count

            if slots <= 0:
                time.sleep(5)
                continue

            # ── 4. 取待拨打任务 ────────────────────────────────
            pending_tasks = (
                db.query(CallTask)
                .filter(
                    CallTask.batch_id == batch_id,
                    CallTask.status == CallStatus.pending,
                )
                .limit(slots)
                .all()
            )

            if not pending_tasks:
                # 没有 pending，也没有 calling → 批次完成
                if calling_count == 0:
                    # 最后一轮：处理未接通重试
                    _handle_no_answer_retries(db, batch_id)
                    # 检查是否还有 pending 任务（重置出来的）
                    still_pending = (
                        db.query(CallTask)
                        .filter(
                            CallTask.batch_id == batch_id,
                            CallTask.status == CallStatus.pending,
                        )
                        .count()
                    )
                    if still_pending == 0:
                        logger.info(f"批次 {batch_id} 所有任务已处理完毕")
                        break
                else:
                    # 还有 calling 中的任务，等待回调
                    _handle_stale_calling(db, batch_id)
                time.sleep(5)
                continue

            # ── 5. 发起呼叫 ────────────────────────────────────
            for task in pending_tasks:
                task.status = CallStatus.calling
                task.call_count = (task.call_count or 0) + 1
                task.called_at = datetime.now()
                db.commit()

                phone = task.patient.phone
                task_id = task.id

                call_id = adapter.initiate_call(task_id, phone)
                if not call_id:
                    task.status = CallStatus.failed
                    task.notes = "API 发起呼叫失败"
                    db.commit()
                    logger.warning(f"[{phone}] 发起失败")
                else:
                    logger.info(f"[{phone}] 已发起，call_id={call_id}")

            # 处理超时任务 & 待重拨任务
            _handle_stale_calling(db, batch_id)
            _handle_no_answer_retries(db, batch_id)

        except Exception as e:
            logger.error(f"拨打引擎循环异常: {e}", exc_info=True)
        finally:
            db.close()

        time.sleep(8)  # 等待 Twilio 回调处理

    _paused_batches.discard(batch_id)
    logger.info(f"===== 批次 {batch_id} 拨打结束 =====")
