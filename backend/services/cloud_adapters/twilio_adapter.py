"""
Twilio 云通信适配器
- 个人账号可用，注册 twilio.com 即可
- 免费试用额度约 $15，可拨打中国号码
- 使用 TTS 语音（无需提前录音），中文效果可接受
"""
import logging
import config

logger = logging.getLogger(__name__)


def initiate_call(task_id: int, phone: str) -> str | None:
    """
    发起外呼，返回 call_sid（Twilio 通话唯一 ID）。

    Twilio 的 IVR 流程完全由 TwiML webhook 驱动：
      发起呼叫 → 用户接听 → Twilio 请求 /api/twilio/voice/{task_id}
      → 播放语音 + 等待按键 → 结果更新到数据库

    返回 None 表示发起失败。
    """
    if not config.PUBLIC_URL:
        logger.error("[Twilio] PUBLIC_URL 未配置，无法接收回调，请先用 ngrok 暴露本地服务")
        return None
    if not all([config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN, config.TWILIO_CALLER_NUMBER]):
        logger.error("[Twilio] 配置不完整，请检查 .env 中的 TWILIO_* 配置项")
        return None

    try:
        from twilio.rest import Client
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

        call = client.calls.create(
            to=phone,
            from_=config.TWILIO_CALLER_NUMBER,
            # 接通后 Twilio 请求此 URL 获取 TwiML 指令
            url=f"{config.PUBLIC_URL}/api/twilio/voice/{task_id}",
            # 通话状态变更时回调（no-answer / busy / completed / failed）
            status_callback=f"{config.PUBLIC_URL}/api/twilio/status/{task_id}",
            status_callback_method="POST",
            status_callback_event=["completed", "no-answer", "busy", "failed"],
            # 30 秒无人接听则放弃
            timeout=30,
        )
        logger.info(f"[Twilio] 已发起呼叫 {phone}, call_sid={call.sid}")
        return call.sid

    except Exception as e:
        logger.error(f"[Twilio] 发起呼叫失败 {phone}: {e}")
        return None
