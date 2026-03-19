"""拨打任务管理 API"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Patient, CallTask, CallStatus
from schemas import TaskCreate, TaskOut, BatchStats, MessageResponse

router = APIRouter(prefix="/api/tasks", tags=["拨打任务管理"])


@router.post("/create", response_model=MessageResponse, summary="创建批次任务")
def create_batch(data: TaskCreate, db: Session = Depends(get_db)):
    """
    创建一个拨打批次，为每个选中的老人生成一条待拨打记录。
    可以通过 patient_ids 指定，或通过 community 按社区筛选。
    """
    batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

    # 确定要拨打的老人列表
    if data.patient_ids:
        patients = db.query(Patient).filter(Patient.id.in_(data.patient_ids)).all()
    elif data.community:
        patients = db.query(Patient).filter(Patient.community.contains(data.community)).all()
    else:
        patients = db.query(Patient).all()

    if not patients:
        raise HTTPException(400, "没有找到符合条件的老人")

    # 为每个老人创建一条任务记录
    for patient in patients:
        task = CallTask(
            batch_id=batch_id,
            patient_id=patient.id,
            status=CallStatus.pending,
        )
        db.add(task)

    db.commit()
    return MessageResponse(message=f"已创建批次，共{len(patients)}条待拨打", batch_id=batch_id)


@router.get("/batches", summary="查询所有批次")
def list_batches(db: Session = Depends(get_db)):
    """返回所有批次及其基本统计"""
    batches = (
        db.query(
            CallTask.batch_id,
            func.count(CallTask.id).label("total"),
            func.min(CallTask.created_at).label("created_at"),
        )
        .group_by(CallTask.batch_id)
        .order_by(func.min(CallTask.created_at).desc())
        .all()
    )
    result = []
    for batch in batches:
        # 统计各状态数量
        stats = _get_batch_stats(db, batch.batch_id)
        result.append({
            "batch_id": batch.batch_id,
            "total": batch.total,
            "created_at": batch.created_at,
            **stats,
        })
    return result


@router.get("/batch/{batch_id}", response_model=list[TaskOut], summary="查询批次详情")
def get_batch_detail(batch_id: str, db: Session = Depends(get_db)):
    tasks = db.query(CallTask).filter(CallTask.batch_id == batch_id).all()
    result = []
    for task in tasks:
        out = TaskOut.model_validate(task)
        out.patient_name = task.patient.name if task.patient else None
        out.patient_phone = task.patient.phone if task.patient else None
        result.append(out)
    return result


@router.post("/batch/{batch_id}/start", summary="启动拨打")
def start_batch(batch_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """启动某批次的自动拨打（后台异步执行）"""
    pending = db.query(CallTask).filter(
        CallTask.batch_id == batch_id,
        CallTask.status == CallStatus.pending,
    ).count()

    if pending == 0:
        raise HTTPException(400, "该批次没有待拨打的记录")

    # 在后台启动拨打引擎
    from services.call_engine import start_calling
    background_tasks.add_task(start_calling, batch_id)

    return {"message": f"已启动拨打，待处理{pending}条", "batch_id": batch_id}


@router.post("/batch/{batch_id}/pause", summary="暂停拨打")
def pause_batch(batch_id: str):
    """暂停某批次的拨打"""
    from services.call_engine import pause_calling
    pause_calling(batch_id)
    return {"message": "已暂停", "batch_id": batch_id}


@router.post("/batch/{batch_id}/resume", summary="恢复拨打")
def resume_batch(batch_id: str):
    """恢复某批次的拨打"""
    from services.call_engine import resume_calling
    resume_calling(batch_id)
    return {"message": "已恢复", "batch_id": batch_id}


@router.get("/pending-transfers", summary="待弹屏转接记录")
def get_pending_transfers(db: Session = Depends(get_db)):
    """获取所有已转人工但尚未创建预约的任务（用于客服弹屏）"""
    from models import Appointment as ApptModel

    transferred_tasks = (
        db.query(CallTask)
        .outerjoin(ApptModel, ApptModel.task_id == CallTask.id)
        .filter(
            CallTask.status == CallStatus.transferred,
            ApptModel.id == None,
        )
        .order_by(CallTask.called_at.desc())
        .all()
    )

    result = []
    for task in transferred_tasks:
        out = TaskOut.model_validate(task)
        out.patient_name = task.patient.name if task.patient else None
        out.patient_phone = task.patient.phone if task.patient else None
        result.append(out)
    return result


@router.get("/batch/{batch_id}/stats", response_model=BatchStats, summary="批次统计")
def get_batch_stats(batch_id: str, db: Session = Depends(get_db)):
    stats = _get_batch_stats(db, batch_id)
    return BatchStats(batch_id=batch_id, **stats)


def _get_batch_stats(db: Session, batch_id: str) -> dict:
    """统计某批次各状态数量"""
    tasks = db.query(CallTask).filter(CallTask.batch_id == batch_id).all()
    stats = {
        "total": len(tasks),
        "pending": 0, "calling": 0, "accepted": 0, "rejected": 0,
        "no_answer": 0, "to_schedule": 0, "transferred": 0, "failed": 0,
    }
    for t in tasks:
        if t.status in stats:
            stats[t.status] += 1
    return stats
