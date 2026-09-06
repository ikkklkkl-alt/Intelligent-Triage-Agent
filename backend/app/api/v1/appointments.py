from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload
from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import Appointment, AppointmentStatus, Role, Schedule, User
from app.schemas import AppointmentIn, AppointmentOut

router = APIRouter(prefix="/appointments", tags=["appointments"])

def _to_out(a: Appointment) -> AppointmentOut:
    s = a.schedule
    return AppointmentOut(id=a.id, status=a.status.value, created_at=a.created_at, patient_name=a.patient.full_name,
        doctor_name=s.doctor.user.full_name, department_name=s.doctor.department.name, work_date=s.work_date, slot=s.slot.value)

async def _get_appt(db: AsyncSession, appt_id: int) -> Appointment:
    appt = (await db.execute(select(Appointment).where(Appointment.id == appt_id))).scalar_one()
    await db.refresh(appt, attribute_names=["patient", "schedule"])
    await db.refresh(appt.schedule, attribute_names=["doctor"])
    await db.refresh(appt.schedule.doctor, attribute_names=["user", "department"])
    return appt

@router.post("", response_model=AppointmentOut)
async def book(data: AppointmentIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.patient))):
    schedule = await db.scalar(select(Schedule).where(Schedule.id == data.schedule_id).options(noload("*")).with_for_update())
    if not schedule: raise HTTPException(404, "排班不存在")
    if schedule.booked >= schedule.capacity: raise HTTPException(400, "该时段号源已满")
    dup = await db.scalar(select(Appointment).where(Appointment.patient_id == user.id, Appointment.schedule_id == schedule.id, Appointment.status == AppointmentStatus.booked))
    if dup: raise HTTPException(400, "您已预约过该时段")
    schedule.booked += 1
    appt = Appointment(patient_id=user.id, schedule_id=schedule.id, triage_session_id=data.triage_session_id)
    db.add(appt); await db.commit(); appt = await _get_appt(db, appt.id); return _to_out(appt)

@router.get("", response_model=list[AppointmentOut])
async def my_appointments(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Appointment).order_by(Appointment.id.desc())
    if user.role == Role.patient: stmt = stmt.where(Appointment.patient_id == user.id)
    elif user.role != Role.admin: raise HTTPException(403, "无权访问")
    return [_to_out(a) for a in (await db.execute(stmt)).scalars()]

@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel(appointment_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.patient))):
    appt = await db.get(Appointment, appointment_id)
    if not appt or appt.patient_id != user.id: raise HTTPException(404, "预约不存在")
    if appt.status != AppointmentStatus.booked: raise HTTPException(400, "当前状态不可取消")
    appt.status = AppointmentStatus.cancelled
    schedule = await db.get(Schedule, appt.schedule_id); schedule.booked = max(0, schedule.booked - 1)
    await db.commit(); appt = await _get_appt(db, appt.id); return _to_out(appt)
