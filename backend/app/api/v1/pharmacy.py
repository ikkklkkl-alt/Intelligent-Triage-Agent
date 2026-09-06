from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import require_roles
from app.db.session import get_db
from app.models import DispenseRecord, Prescription, PrescriptionStatus, Role, User
from app.schemas import PrescriptionOut

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])

def _out(p):
    out = PrescriptionOut.model_validate(p); out.patient_name = p.encounter.patient.full_name; return out

@router.get("/pending", response_model=list[PrescriptionOut])
async def pending(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.pharmacist))):
    return [_out(p) for p in (await db.execute(select(Prescription).where(Prescription.status == PrescriptionStatus.paid).order_by(Prescription.id))).scalars()]

@router.post("/{prescription_id}/dispense", response_model=PrescriptionOut)
async def dispense(prescription_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.pharmacist))):
    pres = await db.get(Prescription, prescription_id)
    if not pres: raise HTTPException(404, "处方不存在")
    if pres.status != PrescriptionStatus.paid: raise HTTPException(400, "处方未缴费或已发药")
    pres.status = PrescriptionStatus.dispensed; db.add(DispenseRecord(prescription_id=pres.id, pharmacist_id=user.id))
    await db.commit(); await db.refresh(pres); return _out(pres)
