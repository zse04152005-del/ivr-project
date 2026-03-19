"""
Mock 模拟适配器 —— 无需任何云通信账号，直接模拟呼叫结果

用途：本地开发 / 功能测试，可完整走通：
  发起任务 → 模拟通话 → 状态更新 → 弹屏转接 → 预约登记 → 报表导出

模拟结果概率（可通过 MOCK_RESULT_WEIGHTS 调整）：
  transferred  40%  — 按 1-1，转人工（触发弹屏）
  to_schedule  25%  — 按 1-2，下次再约
  rejected     15%  — 按 2，拒绝
  no_answer    20%  — 无人接听（会自动重拨）
"""
import logging
import random
import threading
import time
import uuid

logger = logging.getLogger(__name__)

# 模拟结果权重，可按需调整
MOCK_RESULT_WEIGHTS = [
    ("transferred", "1-1", True,  "模拟：已转人工预约",        40),
    ("to_schedule", "1-2", False, "模拟：同意体检，下次再约",  25),
    ("rejected",    "2",   False, "模拟：拒绝体检",            15),
    ("no_answer",   None,  False, "模拟：无人接听",            20),
]

# 模拟通话耗时范围（秒）
MOCK_CALL_DELAY_MIN = 3
MOCK_CALL_DELAY_MAX = 8


def _simulate_call_result(task_id: int):
    """在后台线程中模拟通话过程，完成后直接更新数据库。"""
    delay = random.uniform(MOCK_CALL_DELAY_MIN, MOCK_CALL_DELAY_MAX)
    time.sleep(delay)

    # 按权重随机选取结果
    population = [(s, k, t, n) for s, k, t, n, w in MOCK_RESULT_WEIGHTS for _ in range(w)]
    status_str, key_pressed, transferred, notes = random.choice(population)

    from database import SessionLocal
    from models import CallTask, CallStatus

    db = SessionLocal()
    try:
        task = db.get(CallTask, task_id)
        if not task or task.status != CallStatus.calling:
            return  # 任务已被其他逻辑处理

        task.status = getattr(CallStatus, status_str)
        task.key_pressed = key_pressed
        task.transferred = transferred
        task.notes = notes
        db.commit()
        logger.info(
            f"[Mock] task_id={task_id} 模拟结果: "
            f"status={status_str} key={key_pressed} ({delay:.1f}s)"
        )
    except Exception as e:
        logger.error(f"[Mock] 更新任务状态失败 task_id={task_id}: {e}")
    finally:
        db.close()


def initiate_call(task_id: int, phone: str) -> str | None:
    """
    模拟发起外呼。
    立即返回一个假的 call_id，后台线程在几秒后更新任务状态。
    """
    fake_call_id = f"mock-{uuid.uuid4().hex[:12]}"
    logger.info(f"[Mock] 模拟呼叫 {phone}，task_id={task_id}，call_id={fake_call_id}")

    t = threading.Thread(
        target=_simulate_call_result,
        args=(task_id,),
        daemon=True,
    )
    t.start()

    return fake_call_id
