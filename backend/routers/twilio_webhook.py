"""
Twilio IVR 回调路由

Twilio 接通后回调此处的接口，通过 TwiML 指令驱动 IVR 流程：

  用户接通
    → POST /api/twilio/voice/{task_id}
        播放开场白 + 等待按键（按1能来 / 按2不来）
    → POST /api/twilio/dtmf/{task_id}/layer1
        按1 → 播放第二层（现在约按1 / 下次约按2）
             → POST /api/twilio/dtmf/{task_id}/layer2
                 按1 → 转接人工（<Dial>）→ status=transferred
                 按2 → status=to_schedule
        按2 → status=rejected
        无键 → status=no_answer
    → POST /api/twilio/status/{task_id}
        通话结束状态（no-answer / busy / failed / completed）
"""
import logging
from typing import Optional

from fastapi import APIRouter, Form, Response

import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/twilio", tags=["Twilio回调"])


def _twiml(xml_body: str) -> Response:
    return Response(content=xml_body.strip(), media_type="application/xml")


@router.post("/voice/{task_id}", summary="Twilio 接通回调 — 播放开场白")
async def twilio_voice(task_id: int):
    """用户接通后 Twilio 请求此接口，返回 TwiML 播放开场白并采集第一层按键。"""
    from database import SessionLocal
    from models import CallTask, CallStatus
    from datetime import datetime

    db = SessionLocal()
    try:
        task = db.get(CallTask, task_id)
        if not task:
            return _twiml("<Response><Hangup/></Response>")

        # 若引擎还没来得及更新状态，在此兜底
        if task.status == CallStatus.pending:
            task.status = CallStatus.calling
            task.called_at = datetime.now()
            task.call_count = (task.call_count or 0) + 1
            db.commit()
    finally:
        db.close()

    action = f"{config.PUBLIC_URL}/api/twilio/dtmf/{task_id}/layer1"
    timeout = config.DTMF_TIMEOUT

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather numDigits="1" action="{action}" method="POST" timeout="{timeout}">
    <Say language="zh-CN" voice="alice">
      您好，这里是社区健康服务中心。现在通知您参加今年的免费体检活动。
      如果您愿意参加体检，请按 1；
      如果不需要参加，请按 2。
      请您现在做出选择。
    </Say>
  </Gather>
  <Say language="zh-CN" voice="alice">您好，我们没有收到您的按键，请再听一遍。</Say>
  <Gather numDigits="1" action="{action}" method="POST" timeout="{timeout}">
    <Say language="zh-CN" voice="alice">
      如果您愿意参加体检，请按 1；
      如果不需要参加，请按 2。
    </Say>
  </Gather>
  <Say language="zh-CN" voice="alice">感谢您的接听，再见。</Say>
  <Hangup/>
</Response>"""
    return _twiml(xml)


@router.post("/dtmf/{task_id}/layer1", summary="第一层按键处理（愿意/不愿意）")
async def twilio_dtmf_layer1(
    task_id: int,
    Digits: Optional[str] = Form(default=None),
):
    """
    按 1 → 进入第二层（现在约 / 下次约）
    按 2 → 拒绝体检，status=rejected
    无键 → status=no_answer，挂断
    """
    from database import SessionLocal
    from models import CallTask, CallStatus

    db = SessionLocal()
    try:
        task = db.get(CallTask, task_id)
        if not task:
            return _twiml("<Response><Hangup/></Response>")

        if Digits == "2":
            task.status = CallStatus.rejected
            task.key_pressed = "2"
            task.notes = "拒绝体检"
            db.commit()
            return _twiml("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say language="zh-CN" voice="alice">
    感谢您的回复，如果您以后需要体检，欢迎随时联系我们，再见。
  </Say>
  <Hangup/>
</Response>""")

        if Digits == "1":
            task.key_pressed = "1"
            db.commit()
            action = f"{config.PUBLIC_URL}/api/twilio/dtmf/{task_id}/layer2"
            timeout = config.DTMF_TIMEOUT
            return _twiml(f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather numDigits="1" action="{action}" method="POST" timeout="{timeout}">
    <Say language="zh-CN" voice="alice">
      非常感谢您愿意参加体检！
      如果您希望现在转接人工客服，由工作人员帮您预约具体时间，请按 1；
      如果您希望我们稍后再联系您安排时间，请按 2。
    </Say>
  </Gather>
  <Say language="zh-CN" voice="alice">
    感谢您的接听，我们会安排工作人员再次与您联系，再见。
  </Say>
  <Hangup/>
</Response>""")

        # 无键或其他
        task.status = CallStatus.no_answer
        task.notes = "第一层无有效按键"
        db.commit()
        return _twiml("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say language="zh-CN" voice="alice">感谢您的接听，再见。</Say>
  <Hangup/>
</Response>""")
    finally:
        db.close()


@router.post("/dtmf/{task_id}/layer2", summary="第二层按键处理（现在约/下次约）")
async def twilio_dtmf_layer2(
    task_id: int,
    Digits: Optional[str] = Form(default=None),
):
    """
    按 1 → 转接人工客服，status=transferred
    按 2 → 待约，status=to_schedule
    无键 → 默认待约
    """
    from database import SessionLocal
    from models import CallTask, CallStatus

    db = SessionLocal()
    try:
        task = db.get(CallTask, task_id)
        if not task:
            return _twiml("<Response><Hangup/></Response>")

        if Digits == "1":
            task.status = CallStatus.transferred
            task.key_pressed = "1-1"
            task.transferred = True
            task.notes = "已转人工预约"
            db.commit()

            agent = config.AGENT_PHONE_NUMBER
            if agent:
                caller_id = config.TWILIO_CALLER_NUMBER
                xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say language="zh-CN" voice="alice">好的，正在为您转接人工客服，请稍候。</Say>
  <Dial timeout="30" callerId="{caller_id}">
    <Number>{agent}</Number>
  </Dial>
  <Say language="zh-CN" voice="alice">
    很抱歉，客服暂时无人接听，我们会尽快与您联系，再见。
  </Say>
</Response>"""
            else:
                xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say language="zh-CN" voice="alice">
    好的，我们已记录您的预约意愿，工作人员会尽快与您联系安排时间，再见。
  </Say>
  <Hangup/>
</Response>"""
            return _twiml(xml)

        # 按 2 或无键 → 待约
        key = "1-2" if Digits == "2" else "1-?"
        notes = "同意体检，下次再约" if Digits == "2" else f"同意体检，第二层按键={Digits}，默认待约"
        task.status = CallStatus.to_schedule
        task.key_pressed = key
        task.notes = notes
        db.commit()

        return _twiml("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say language="zh-CN" voice="alice">
    好的，我们已记录您的意愿，稍后会再次联系您安排体检时间，感谢您的配合，再见。
  </Say>
  <Hangup/>
</Response>""")
    finally:
        db.close()


@router.post("/status/{task_id}", summary="Twilio 通话状态回调")
async def twilio_status(
    task_id: int,
    CallStatus: Optional[str] = Form(default=None),
    CallSid: Optional[str] = Form(default=None),
    CallDuration: Optional[str] = Form(default=None),
):
    """通话结束后 Twilio 推送最终状态（no-answer / busy / failed / completed）。"""
    from database import SessionLocal
    from models import CallTask, CallStatus as DBCallStatus

    logger.info(
        f"[Twilio] 状态回调 task_id={task_id} "
        f"CallStatus={CallStatus} sid={CallSid} duration={CallDuration}s"
    )

    db = SessionLocal()
    try:
        task = db.get(CallTask, task_id)
        if not task:
            return {"ok": True}

        # 只处理仍在 calling 状态的任务（已被 DTMF 回调处理过的不覆盖）
        if task.status == DBCallStatus.calling:
            if CallStatus == "no-answer":
                task.status = DBCallStatus.no_answer
                task.notes = "无人接听"
            elif CallStatus == "busy":
                task.status = DBCallStatus.no_answer
                task.notes = "线路忙"
            elif CallStatus == "failed":
                task.status = DBCallStatus.failed
                task.notes = "呼叫失败"
            # completed 由 DTMF 处理，不覆盖
            db.commit()

        return {"ok": True}
    finally:
        db.close()
