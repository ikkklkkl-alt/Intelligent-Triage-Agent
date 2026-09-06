from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import (Appointment, AppointmentStatus, DoctorProfile, Encounter, EncounterStatus,
    LabOrder, Payment, PaymentKind, Prescription, PrescriptionItem, Role, Schedule, User)
from app.schemas import (AppointmentOut, EncounterIn, EncounterOut, EncounterUpdate,
    LabOrderIn, LabOrderOut, PrescriptionIn, PrescriptionOut)

router = APIRouter(tags=["encounters"])

async def _doctor_profile(db, user):
    profile = await db.scalar(select(DoctorProfile).where(DoctorProfile.user_id == user.id))
    if not profile: raise HTTPException(400, "当前账号未绑定医生档案")
    return profile

def _enc_out(e):
    return EncounterOut(id=e.id, appointment_id=e.appointment_id, patient_id=e.patient_id,
        patient_name=e.patient.full_name, chief_complaint=e.chief_complaint, diagnosis=e.diagnosis,
        plan=e.plan, status=e.status.value, created_at=e.created_at)

@router.get("/doctor/worklist", response_model=list[AppointmentOut])
async def worklist(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.doctor))):
    profile = await _doctor_profile(db, user)
    appts = (await db.execute(select(Appointment).join(Schedule, Appointment.schedule_id == Schedule.id)
        .where(Schedule.doctor_id == profile.id, Schedule.work_date == date.today(), Appointment.status == AppointmentStatus.booked)
        .order_by(Appointment.id))).scalars()
    return [AppointmentOut(id=a.id, status=a.status.value, created_at=a.created_at, patient_name=a.patient.full_name,
        doctor_name=user.full_name, department_name=a.schedule.doctor.department.name,
        work_date=a.schedule.work_date, slot=a.schedule.slot.value) for a in appts]

@router.post("/encounters", response_model=EncounterOut)
async def start_encounter(data: EncounterIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.doctor))):
    profile = await _doctor_profile(db, user)
    appt = await db.get(Appointment, data.appointment_id)
    if not appt or appt.schedule.doctor_id != profile.id: raise HTTPException(404, "预约不存在或不属于当前医生")
    existing = await db.scalar(select(Encounter).where(Encounter.appointment_id == appt.id))
    if existing: return _enc_out(existing)
    enc = Encounter(appointment_id=appt.id, doctor_id=profile.id, patient_id=appt.patient_id)
    db.add(enc); await db.commit(); await db.refresh(enc); return _enc_out(enc)

@router.get("/encounters/{encounter_id}", response_model=EncounterOut)
async def get_encounter(encounter_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    enc = await db.get(Encounter, encounter_id)
    if not enc: raise HTTPException(404, "病历不存在")
    if user.role == Role.patient and enc.patient_id != user.id: raise HTTPException(403, "无权访问")
    return _enc_out(enc)

@router.put("/encounters/{encounter_id}", response_model=EncounterOut)
async def update_encounter(encounter_id: int, data: EncounterUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.doctor))):
    enc = await db.get(Encounter, encounter_id)
    if not enc: raise HTTPException(404, "病历不存在")
    for f in ("chief_complaint", "diagnosis", "plan"):
        v = getattr(data, f)
        if v is not None: setattr(enc, f, v)
    if data.close:
        enc.status = EncounterStatus.closed
        appt = await db.get(Appointment, enc.appointment_id); appt.status = AppointmentStatus.completed
    await db.commit(); await db.refresh(enc); return _enc_out(enc)

@router.get("/patient/encounters", response_model=list[EncounterOut])
async def my_encounters(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.patient))):
    return [_enc_out(e) for e in (await db.execute(select(Encounter).where(Encounter.patient_id == user.id).order_by(Encounter.id.desc()))).scalars()]

@router.post("/encounters/{encounter_id}/prescriptions", response_model=PrescriptionOut)
async def create_prescription(encounter_id: int, data: PrescriptionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.doctor))):
    enc = await db.get(Encounter, encounter_id)
    if not enc: raise HTTPException(404, "病历不存在")
    total = sum(i.price * i.quantity for i in data.items)
    pres = Prescription(encounter_id=enc.id, total_fee=total); db.add(pres); await db.flush()
    for i in data.items: db.add(PrescriptionItem(prescription_id=pres.id, drug_name=i.drug_name, spec=i.spec, quantity=i.quantity, price=i.price, usage=i.usage))
    db.add(Payment(patient_id=enc.patient_id, kind=PaymentKind.prescription, ref_id=pres.id, amount=total))
    await db.commit(); await db.refresh(pres); return PrescriptionOut.model_validate(pres)

@router.post("/encounters/{encounter_id}/lab-orders", response_model=LabOrderOut)
async def create_lab_order(encounter_id: int, data: LabOrderIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.doctor))):
    enc = await db.get(Encounter, encounter_id)
    if not enc: raise HTTPException(404, "病历不存在")
    order = LabOrder(encounter_id=enc.id, item_name=data.item_name, fee=data.fee); db.add(order); await db.flush()
    db.add(Payment(patient_id=enc.patient_id, kind=PaymentKind.lab, ref_id=order.id, amount=data.fee))
    await db.commit(); await db.refresh(order); return LabOrderOut.model_validate(order)

@router.get("/encounters/{encounter_id}/orders")
async def encounter_orders(encounter_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    enc = await db.get(Encounter, encounter_id)
    if not enc: raise HTTPException(404, "病历不存在")
    if user.role == Role.patient and enc.patient_id != user.id: raise HTTPException(403, "无权访问")
    pres = (await db.execute(select(Prescription).where(Prescription.encounter_id == enc.id))).scalars()
    labs = (await db.execute(select(LabOrder).where(LabOrder.encounter_id == enc.id))).scalars()
    return {"prescriptions": [PrescriptionOut.model_validate(p).model_dump() for p in pres],
            "lab_orders": [LabOrderOut.model_validate(o).model_dump() for o in labs]}
