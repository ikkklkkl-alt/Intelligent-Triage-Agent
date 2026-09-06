from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import (LabOrder, LabOrderStatus, Payment, PaymentKind, PaymentStatus,
    Prescription, PrescriptionStatus, Role, User)
from app.schemas import PaymentOut

router = APIRouter(prefix="/billing", tags=["billing"])

def _out(p):
    return PaymentOut(id=p.id, kind=p.kind.value, ref_id=p.ref_id, amount=p.amount, status=p.status.value,
        patient_name=p.patient.full_name, created_at=p.created_at)

@router.get("/pending", response_model=list[PaymentOut])
async def pending(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.cashier))):
    return [_out(p) for p in (await db.execute(select(Payment).where(Payment.status == PaymentStatus.pending).order_by(Payment.id))).scalars()]

@router.get("/mine", response_model=list[PaymentOut])
async def my_payments(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.patient))):
    return [_out(p) for p in (await db.execute(select(Payment).where(Payment.patient_id == user.id).order_by(Payment.id.desc()))).scalars()]

@router.post("/{payment_id}/pay", response_model=PaymentOut)
async def collect(payment_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.cashier))):
    payment = await db.get(Payment, payment_id)
    if not payment: raise HTTPException(404, "缴费单不存在")
    if payment.status == PaymentStatus.paid: raise HTTPException(400, "该单已缴费")
    payment.status = PaymentStatus.paid; payment.cashier_id = user.id; payment.paid_at = datetime.now(timezone.utc)
    if payment.kind == PaymentKind.prescription:
        pres = await db.get(Prescription, payment.ref_id)
        if pres: pres.status = PrescriptionStatus.paid
    else:
        order = await db.get(LabOrder, payment.ref_id)
        if order: order.status = LabOrderStatus.paid
    await db.commit(); await db.refresh(payment); return _out(payment)
