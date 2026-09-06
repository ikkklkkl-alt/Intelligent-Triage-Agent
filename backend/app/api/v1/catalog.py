from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Department, DoctorProfile, Schedule
from app.schemas import DepartmentOut, DoctorOut, ScheduleOut

router = APIRouter(tags=["catalog"])

@router.get("/departments", response_model=list[DepartmentOut])
async def list_departments(db: AsyncSession = Depends(get_db)):
    return list((await db.execute(select(Department).order_by(Department.id))).scalars())

@router.get("/doctors", response_model=list[DoctorOut])
async def list_doctors(department_id: int | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(DoctorProfile)
    if department_id: stmt = stmt.where(DoctorProfile.department_id == department_id)
    doctors = (await db.execute(stmt)).scalars()
    return [DoctorOut(id=d.id, title=d.title, bio=d.bio, full_name=d.user.full_name, department_id=d.department_id, department_name=d.department.name) for d in doctors]

@router.get("/doctors/{doctor_id}/schedules", response_model=list[ScheduleOut])
async def doctor_schedules(doctor_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Schedule).where(Schedule.doctor_id == doctor_id, Schedule.work_date >= date.today(),
        Schedule.work_date <= date.today() + timedelta(days=7)).order_by(Schedule.work_date, Schedule.slot)
    return list((await db.execute(stmt)).scalars())
