"""Pydantic 请求/响应模型"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


# ========== 老人信息 ==========
class PatientBase(BaseModel):
    name: str = Field(..., max_length=50, description="姓名")
    phone: str = Field(..., max_length=20, description="电话号码")
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")
    community: Optional[str] = Field(None, max_length=100, description="所属社区")

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    community: Optional[str] = None

class PatientOut(PatientBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ========== 拨打任务 ==========
class TaskCreate(BaseModel):
    """创建批次任务"""
    patient_ids: Optional[List[int]] = Field(None, description="指定患者ID列表")
    community: Optional[str] = Field(None, description="按社区筛选（与patient_ids二选一）")

class TaskOut(BaseModel):
    id: int
    batch_id: str
    patient_id: int
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    status: str
    call_count: int
    called_at: Optional[datetime] = None
    key_pressed: Optional[str] = None
    transferred: bool
    notes: Optional[str] = None
    class Config:
        from_attributes = True

class BatchStats(BaseModel):
    """批次统计"""
    batch_id: str
    total: int = 0
    pending: int = 0
    calling: int = 0
    accepted: int = 0       # 按了1（含转人工和待约）
    rejected: int = 0       # 按了2
    no_answer: int = 0      # 未接/未响应
    to_schedule: int = 0    # 按了1-2（下次约）
    transferred: int = 0    # 按了1-1（转人工）
    failed: int = 0


# ========== 预约 ==========
class AppointmentCreate(BaseModel):
    patient_id: int
    task_id: Optional[int] = None
    appointment_date: date
    appointment_time: str = Field(..., description="如 09:00-10:00")
    operator: Optional[str] = None

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = None
    operator: Optional[str] = None

class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    task_id: Optional[int] = None
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = None
    operator: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ========== 统计总览 ==========
class OverviewStats(BaseModel):
    total_patients: int = 0
    total_calls: int = 0
    connected: int = 0          # 接通数
    connect_rate: float = 0.0   # 接通率
    accepted: int = 0           # 同意
    accept_rate: float = 0.0    # 同意率
    rejected: int = 0
    no_answer: int = 0
    to_schedule: int = 0
    transferred: int = 0
    total_appointments: int = 0


# ========== 通用响应 ==========
class ImportResult(BaseModel):
    success: int = 0
    failed: int = 0
    errors: List[str] = []

class MessageResponse(BaseModel):
    message: str
    batch_id: Optional[str] = None
