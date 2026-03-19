"""预约管理 API"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Appointment, CallTask
from schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut, OverviewStats
from models import Patient

router = APIRouter(prefix="/api/appointments", tags=["预约管理"])


@router.post("", response_model=AppointmentOut, summary="创建预约")
def create_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):
    """人工客服创建预约记录"""
    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    if not patient:
        raise HTTPException(404, "老人不存在")

    appt = Appointment(**data.model_dump())
    db.add(appt)

    # 如果关联了任务，更新任务状态
    if data.task_id:
        task = db.query(CallTask).filter(CallTask.id == data.task_id).first()
        if task:
            task.status = "accepted"
            task.notes = f"已预约 {data.appointment_date} {data.appointment_time}"

    db.commit()
    db.refresh(appt)

    out = AppointmentOut.model_validate(appt)
    out.patient_name = patient.name
    out.patient_phone = patient.phone
    return out


@router.get("", response_model=list[AppointmentOut], summary="查询预约列表")
def list_appointments(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Appointment)
    if start_date:
        query = query.filter(Appointment.appointment_date >= start_date)
    if end_date:
        query = query.filter(Appointment.appointment_date <= end_date)

    appointments = query.order_by(Appointment.appointment_date.desc()).offset((page-1)*size).limit(size).all()

    result = []
    for appt in appointments:
        out = AppointmentOut.model_validate(appt)
        out.patient_name = appt.patient.name if appt.patient else None
        out.patient_phone = appt.patient.phone if appt.patient else None
        result.append(out)
    return result


@router.get("/date/{query_date}", summary="查询某天预约")
def get_appointments_by_date(query_date: date, db: Session = Depends(get_db)):
    appointments = db.query(Appointment).filter(Appointment.appointment_date == query_date).all()
    result = []
    for appt in appointments:
        out = AppointmentOut.model_validate(appt)
        out.patient_name = appt.patient.name if appt.patient else None
        out.patient_phone = appt.patient.phone if appt.patient else None
        result.append(out)
    return {"date": query_date, "count": len(result), "appointments": result}


@router.put("/{appt_id}", response_model=AppointmentOut, summary="修改预约")
def update_appointment(appt_id: int, data: AppointmentUpdate, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(404, "预约不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(appt, key, value)
    db.commit()
    db.refresh(appt)
    out = AppointmentOut.model_validate(appt)
    out.patient_name = appt.patient.name if appt.patient else None
    out.patient_phone = appt.patient.phone if appt.patient else None
    return out


@router.delete("/{appt_id}", summary="取消预约")
def delete_appointment(appt_id: int, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(404, "预约不存在")
    db.delete(appt)
    db.commit()
    return {"message": "已取消"}
