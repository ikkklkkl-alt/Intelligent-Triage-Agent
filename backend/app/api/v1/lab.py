from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import Encounter, LabOrder, LabOrderStatus, LabReport, Role, User
from app.schemas import LabOrderOut, LabReportIn, LabReportOut
from app.tasks.report_tasks import interpret_lab_report

router = APIRouter(tags=["lab"])

@router.get("/lab/orders", response_model=list[LabOrderOut])
async def pending_orders(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.lab))):
    orders = (await db.execute(select(LabOrder).where(LabOrder.status == LabOrderStatus.paid).order_by(LabOrder.id))).scalars()
    return [LabOrderOut(id=o.id, encounter_id=o.encounter_id, item_name=o.item_name, fee=o.fee, status=o.status.value,
        created_at=o.created_at, patient_name=o.encounter.patient.full_name) for o in orders]

@router.post("/lab/orders/{order_id}/report", response_model=LabReportOut)
async def submit_report(order_id: int, data: LabReportIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.lab))):
    order = await db.get(LabOrder, order_id)
    if not order: raise HTTPException(404, "检验单不存在")
    if order.status != LabOrderStatus.paid: raise HTTPException(400, "该检验单未缴费或已出报告")
    report = LabReport(lab_order_id=order.id, raw_text=data.raw_text, items_json=data.items_json, created_by=user.id)
    order.status = LabOrderStatus.reported; db.add(report); await db.commit(); await db.refresh(report)
    interpret_lab_report.delay(report.id)
    return LabReportOut(id=report.id, lab_order_id=order.id, item_name=order.item_name, raw_text=report.raw_text,
        items_json=report.items_json, ai_status=report.ai_status.value, ai_summary=report.ai_summary,
        ai_degraded=report.ai_degraded, created_at=report.created_at)

@router.get("/reports/{report_id}", response_model=LabReportOut)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    report = await db.get(LabReport, report_id)
    if not report: raise HTTPException(404, "报告不存在")
    order = await db.get(LabOrder, report.lab_order_id); enc = await db.get(Encounter, order.encounter_id)
    if user.role == Role.patient and enc.patient_id != user.id: raise HTTPException(403, "无权访问")
    return LabReportOut(id=report.id, lab_order_id=order.id, item_name=order.item_name, raw_text=report.raw_text,
        items_json=report.items_json, ai_status=report.ai_status.value, ai_summary=report.ai_summary,
        ai_degraded=report.ai_degraded, created_at=report.created_at)

@router.get("/patient/reports", response_model=list[LabReportOut])
async def my_reports(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.patient))):
    rows = (await db.execute(select(LabReport, LabOrder).join(LabOrder, LabReport.lab_order_id == LabOrder.id)
        .join(Encounter, LabOrder.encounter_id == Encounter.id).where(Encounter.patient_id == user.id).order_by(LabReport.id.desc()))).all()
    return [LabReportOut(id=r.id, lab_order_id=o.id, item_name=o.item_name, raw_text=r.raw_text, items_json=r.items_json,
        ai_status=r.ai_status.value, ai_summary=r.ai_summary, ai_degraded=r.ai_degraded, created_at=r.created_at) for r, o in rows]

@router.post("/reports/{report_id}/interpret")
async def rerun_interpret(report_id: int, db: AsyncSession = Depends(get_db),
                          user: User = Depends(require_roles(Role.lab, Role.admin, Role.patient))):
    report = await db.get(LabReport, report_id)
    if not report: raise HTTPException(404, "报告不存在")
    interpret_lab_report.delay(report.id); return {"message": "已重新提交 AI 解读任务"}
