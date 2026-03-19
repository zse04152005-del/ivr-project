"""
阿里云通信适配器（企业账号，生产环境使用）

开通步骤：
  1. 登录 aliyun.com，搜索「语音服务」开通
  2. 企业认证 + 提交外呼资质申请（3~7 工作日）
  3. 申请外显号码
  4. 创建 IVR 流程 或 上传语音文件
  5. 将 AccessKey / 号码填入 .env

安装 SDK：
  pip install alibabacloud-dyvmsapi20170525
"""
import logging
import config

logger = logging.getLogger(__name__)


def initiate_call(task_id: int, phone: str) -> str | None:
    """
    发起外呼，返回阿里云 CallId。
    返回 None 表示发起失败。

    阿里云支持两种外呼方式，根据开通的产品选择其一：

    ── 方案 A: SingleCallByVoice（播放上传的语音文件 + DTMF 回调）──────────────
    适合开通了「语音服务-外呼IVR」的账号，需提前上传 WAV/MP3 文件并获取 VoiceCode。

    ── 方案 B: 智能外呼机器人 StartRobotTask（企业专属，需联系销售开通）─────────
    提供更完整的 IVR 流程管理，适合大规模外呼场景。
    """
    if not all([config.ALIYUN_ACCESS_KEY, config.ALIYUN_ACCESS_SECRET, config.ALIYUN_CALLER_NUMBER]):
        logger.error("[Aliyun] 配置不完整，请检查 .env 中的 ALIYUN_* 配置项")
        return None

    try:
        from alibabacloud_dyvmsapi20170525.client import Client
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_dyvmsapi20170525 import models as dyvms_models

        cfg = open_api_models.Config(
            access_key_id=config.ALIYUN_ACCESS_KEY,
            access_key_secret=config.ALIYUN_ACCESS_SECRET,
            endpoint="dyvmsapi.aliyuncs.com",
        )
        client = Client(cfg)

        # ── 方案 A: SingleCallByVoice ──────────────────────────────────────────
        request = dyvms_models.SingleCallByVoiceRequest(
            called_show_number=config.ALIYUN_CALLER_NUMBER,
            called_number=phone,
            voice_code=config.ALIYUN_VOICE_CODE_OPENING,   # 开场白语音文件 ID
            play_times=2,                                    # 无响应时重播次数
            # 按键事件回调（需配置公网地址）
            dtmf_http_url=f"{config.PUBLIC_URL}/api/callback/dtmf",
            # 通话结束状态回调
            out_id=str(task_id),
        )
        response = client.single_call_by_voice(request)

        if response.body.code == "OK":
            call_id = response.body.call_id
            logger.info(f"[Aliyun] 已发起呼叫 {phone}, call_id={call_id}")
            return call_id
        else:
            logger.error(f"[Aliyun] API 返回错误: {response.body.code} - {response.body.message}")
            return None

    except ImportError:
        logger.error("[Aliyun] SDK 未安装，请执行: pip install alibabacloud-dyvmsapi20170525")
        return None
    except Exception as e:
        logger.error(f"[Aliyun] 发起呼叫失败 {phone}: {e}")
        return None
