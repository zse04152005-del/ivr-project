"""短信服务（可选：拨打前发预告短信）"""
import logging
import config

logger = logging.getLogger(__name__)


def send_notice_sms(phone: str, name: str) -> bool:
    """
    发送体检预告短信（拨打前通知）

    TODO: 对接阿里云短信，需安装 alibabacloud-dysmsapi20170525
    示例：
        pip install alibabacloud-dysmsapi20170525
        from alibabacloud_dysmsapi20170525.client import Client
        from alibabacloud_tea_openapi import models as open_api_models
        ...
    """
    if not config.SMS_ENABLED:
        return False

    message = config.SMS_TEMPLATE.format(name=name)
    logger.info(f"[SMS] 预告短信 → {phone}: {message}")

    # TODO: 实际发送逻辑
    # try:
    #     client = _build_client()
    #     req = SendSmsRequest(
    #         phone_numbers=phone,
    #         sign_name="XX社区",
    #         template_code="SMS_XXXXXXXX",
    #         template_param=json.dumps({"name": name}),
    #     )
    #     client.send_sms(req)
    #     return True
    # except Exception as e:
    #     logger.error(f"[SMS] 发送失败 {phone}: {e}")
    #     return False

    return False


def send_appointment_confirm_sms(phone: str, name: str, date: str, time_slot: str) -> bool:
    """
    发送预约确认短信

    TODO: 实现具体发送逻辑
    """
    if not config.SMS_ENABLED:
        return False

    message = f"【XX社区】{name}您好，您的年度体检已预约在{date} {time_slot}，请准时前来，谢谢。"
    logger.info(f"[SMS] 预约确认 → {phone}: {message}")
    return False
