"""系统配置"""
import os
from dotenv import load_dotenv

load_dotenv()


# ======== 数据库 ========
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ivr_system.db")

# ======== 外呼时间控制 ========
CALL_START_HOUR = 8        # 最早拨打：上午8点
CALL_END_HOUR = 18         # 最晚拨打：下午6点
LUNCH_START = "12:00"      # 午休开始（不拨打）
LUNCH_END = "14:00"        # 午休结束

# ======== IVR 参数 ========
DTMF_TIMEOUT = 18          # 按键等待时间（秒），老人需要更长时间
MAX_RETRY = 3              # 未接通最大重拨次数
RETRY_INTERVAL = 7200      # 重拨间隔（秒），默认2小时
MAX_CONCURRENT = 5         # 最大并发呼叫数
REPEAT_PROMPT = 2          # 无响应时语音重复次数

# ======== 云通信平台配置 ========
# 选择平台：aliyun（生产）/ twilio / mock（本地测试，无需账号）
CALL_PLATFORM = os.getenv("CALL_PLATFORM", "aliyun")

# 公网回调地址（Twilio / 阿里云 回调必须可访问）
# 本地开发时用 ngrok：ngrok http 8000，将生成的 https 地址填入
PUBLIC_URL = os.getenv("PUBLIC_URL", "")

# --- Twilio（个人账号即可，注册 twilio.com 获取）---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_CALLER_NUMBER = os.getenv("TWILIO_CALLER_NUMBER", "")  # Twilio 购买的号码

# --- 阿里云通信（企业账号 + 语音服务资质）---
ALIYUN_ACCESS_KEY = os.getenv("ALIYUN_ACCESS_KEY", "")
ALIYUN_ACCESS_SECRET = os.getenv("ALIYUN_ACCESS_SECRET", "")
ALIYUN_CALLER_NUMBER = os.getenv("ALIYUN_CALLER_NUMBER", "")
ALIYUN_VOICE_CODE_OPENING = os.getenv("ALIYUN_VOICE_CODE_OPENING", "")  # 上传语音文件的 VoiceCode

# ======== 人工客服转接号码 ========
AGENT_PHONE_NUMBER = os.getenv("AGENT_PHONE_NUMBER", "")  # 人工客服接听电话

# ======== 语音文件路径 ========
VOICE_DIR = os.getenv("VOICE_DIR", "./voices")
VOICE_FILES = {
    "opening":      f"{VOICE_DIR}/opening.wav",       # 开场白
    "schedule":     f"{VOICE_DIR}/schedule.wav",       # 预约引导（按1转人工，按2下次约）
    "transferring": f"{VOICE_DIR}/transferring.wav",   # 正在转接
    "rejected":     f"{VOICE_DIR}/rejected.wav",       # 拒绝结束语
    "to_schedule":  f"{VOICE_DIR}/to_schedule.wav",    # 待约结束语
    "no_input":     f"{VOICE_DIR}/no_input.wav",       # 无响应提示
}

# ======== 短信配置（可选，拨打前发预告短信）========
SMS_ENABLED = False
SMS_TEMPLATE = "【XX社区】您好{name}，XX社区健康服务中心将于今天来电通知您的免费体检安排，请注意接听。"
