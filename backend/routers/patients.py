"""老人信息管理 API"""
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from database import get_db
from models import Patient
from schemas import PatientOut, PatientCreate, PatientUpdate, ImportResult
from utils.excel_parser import parse_excel

router = APIRouter(prefix="/api/patients", tags=["老人信息管理"])


@router.post("/import", response_model=ImportResult, summary="Excel批量导入")
async def import_patients(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传Excel文件批量导入老人信息（姓名、电话、年龄、社区）"""
    content = await file.read()
    records, errors = parse_excel(content, file.filename)

    success_count = 0
    for record in records:
        # 检查手机号是否已存在
        existing = db.query(Patient).filter(Patient.phone == record["phone"]).first()
        if existing:
            errors.append(f"{record['name']}（{record['phone']}）：号码已存在，已跳过")
            continue

        patient = Patient(**record)
        db.add(patient)
        success_count += 1

    db.commit()
    return ImportResult(success=success_count, failed=len(records) - success_count, errors=errors)


@router.get("", response_model=list[PatientOut], summary="查询列表")
def list_patients(
    keyword: Optional[str] = Query(None, description="按姓名或社区搜索"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
    response: Response = None,
):
    query = db.query(Patient)
    if keyword:
        query = query.filter(
            or_(Patient.name.contains(keyword), Patient.community.contains(keyword))
        )
    total = query.count()
    patients = query.order_by(Patient.id.desc()).offset((page - 1) * size).limit(size).all()
    response.headers["X-Total-Count"] = str(total)
    return patients


@router.get("/count", summary="统计总数")
def count_patients(db: Session = Depends(get_db)):
    return {"total": db.query(Patient).count()}


@router.get("/{patient_id}", response_model=PatientOut, summary="查询单个")
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "老人信息不存在")
    return patient


@router.put("/{patient_id}", response_model=PatientOut, summary="编辑")
def update_patient(patient_id: int, data: PatientUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "老人信息不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", summary="删除")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "老人信息不存在")
    db.delete(patient)
    db.commit()
    return {"message": "已删除"}
