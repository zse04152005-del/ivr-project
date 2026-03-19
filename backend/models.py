"""数据库模型 —— 3张核心表"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import enum


class CallStatus(str, enum.Enum):
    """呼叫状态枚举"""
    pending = "pending"            # 待拨打
    calling = "calling"            # 拨打中
    accepted = "accepted"          # 同意体检（按了1）
    rejected = "rejected"          # 拒绝体检（按了2）
    no_answer = "no_answer"        # 无人接听 / 未响应
    to_schedule = "to_schedule"    # 同意但下次再约（按了1-2）
    transferred = "transferred"    # 已转人工（按了1-1）
    failed = "failed"              # 呼叫失败（线路问题）


# ========== 表一：老人信息 ==========
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="姓名")
    phone = Column(String(20), nullable=False, unique=True, comment="电话号码")
    age = Column(Integer, comment="年龄")
    community = Column(String(100), comment="所属社区")
    created_at = Column(DateTime, default=datetime.now, comment="录入时间")

    # 关联
    call_tasks = relationship("CallTask", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")


# ========== 表二：拨打任务 ==========
class CallTask(Base):
    __tablename__ = "call_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(50), nullable=False, index=True, comment="批次号")
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    status = Column(String(20), default=CallStatus.pending, comment="状态")
    call_count = Column(Integer, default=0, comment="已拨打次数")
    called_at = Column(DateTime, comment="最近拨打时间")
    key_pressed = Column(String(10), comment="用户按键记录，如 1-1, 1-2, 2")
    transferred = Column(Boolean, default=False, comment="是否已转人工")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.now)

    # 关联
    patient = relationship("Patient", back_populates="call_tasks")
    appointment = relationship("Appointment", back_populates="task", uselist=False)


# ========== 表三：预约记录 ==========
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("call_tasks.id"), comment="关联拨打任务")
    appointment_date = Column(Date, comment="预约日期")
    appointment_time = Column(String(20), comment="预约时间段，如 09:00-10:00")
    operator = Column(String(50), comment="操作人员（人工客服）")
    created_at = Column(DateTime, default=datetime.now)

    # 关联
    patient = relationship("Patient", back_populates="appointments")
    task = relationship("CallTask", back_populates="appointment")
