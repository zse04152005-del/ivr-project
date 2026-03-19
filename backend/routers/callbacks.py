"""阿里云通信回调接口（Webhook）"""
import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from models import CallTask, CallStatus, Patient, Appointment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/callback", tags=["回调接口"])


def _find_active_task(db: Session, phone: str):
    """根据手机号找到当前拨打中的任务"""
    patient = db.query(Patient).filter(Patient.phone == phone).first()
    if not patient:
        return None
    return (
        db.query(CallTask)
        .filter(
            CallTask.patient_id == patient.id,
            CallTask.status == CallStatus.calling,
        )
        .order_by(CallTask.called_at.desc())
        .first()
    )


@router.post("/call-status", summary="呼叫状态回调")
async def call_status_callback(request: Request, db: Session = Depends(get_db)):
    """
    阿里云通信回调：呼叫状态变更通知

    阿里云回调字段（表单格式）：
      CallId        呼叫ID
      CalledNumber  被叫号码
      Status        ANSWERED / HANGUP / NO_ANSWER / BUSY / CANCEL
      Duration      通话时长（秒）
    """
    try:
        data = dict(await request.form())
    except Exception:
        data = await request.json()

    logger.info(f"[Callback] call-status: {data}")

    called_number = str(data.get("CalledNumber", "")).strip()
    status = str(data.get("Status", "")).upper()

    import config
    task = _find_active_task(db, called_number)
    if not task:
        logger.warning(f"[Callback] 未找到拨打中任务，号码: {called_number}")
        return {"code": "OK"}

    if status in ("NO_ANSWER", "BUSY", "CANCEL", "FAILED"):
        if task.call_count < config.MAX_RETRY:
            task.status = CallStatus.pending
            task.notes = f"第{task.call_count}次未接通({status})，待重拨"
        else:
            task.status = CallStatus.no_answer
            task.notes = f"已重拨{task.call_count}次，最终未接通"
    elif status == "HANGUP":
        # 正常挂机：若按键已记录则状态已由 dtmf 回调更新；否则标记未响应
        if task.status == CallStatus.calling:
            task.status = CallStatus.no_answer
            task.notes = "通话已挂机（未收到有效按键）"

    db.commit()
    return {"code": "OK"}


@router.post("/dtmf", summary="按键事件回调")
async def dtmf_callback(request: Request, db: Session = Depends(get_db)):
    """
    阿里云通信回调：IVR 按键事件

    回调字段：
      CallId        呼叫ID
      CalledNumber  被叫号码
      Dtmf          用户按下的键（1 / 2）
      Stage         IVR阶段：layer1（第一层）/ layer2（第二层）
    """
    try:
        data = dict(await request.form())
    except Exception:
        data = await request.json()

    logger.info(f"[Callback] dtmf: {data}")

    called_number = str(data.get("CalledNumber", "")).strip()
    dtmf = str(data.get("Dtmf", "")).strip()
    stage = str(data.get("Stage", "layer1"))

    task = _find_active_task(db, called_number)
    if not task or not dtmf:
        return {"code": "OK"}

    if stage == "layer1":
        task.key_pressed = dtmf
        if dtmf == "2":
            task.status = CallStatus.rejected
            task.notes = "拒绝体检"
        # dtmf == "1" → 等待 layer2 回调，状态保持 calling
    elif stage == "layer2":
        task.key_pressed = f"1-{dtmf}"
        if dtmf == "1":
            task.status = CallStatus.transferred
            task.transferred = True
            task.notes = "已转人工预约"
        else:
            task.status = CallStatus.to_schedule
            task.notes = "同意体检，下次再约时间"

    db.commit()
    return {"code": "OK"}
