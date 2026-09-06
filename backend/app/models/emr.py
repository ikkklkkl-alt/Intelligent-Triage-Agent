import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class EncounterStatus(str, enum.Enum):
    open = "open"
    closed = "closed"

class Encounter(Base):
    __tablename__ = "encounters"
    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), unique=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctor_profiles.id"))
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    chief_complaint: Mapped[str | None] = mapped_column(Text)
    diagnosis: Mapped[str | None] = mapped_column(Text)
    plan: Mapped[str | None] = mapped_column(Text)
    status: Mapped[EncounterStatus] = mapped_column(
        Enum(EncounterStatus, native_enum=False, length=8), default=EncounterStatus.open)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    patient = relationship("User", lazy="joined")
    doctor = relationship("DoctorProfile", lazy="joined")

class PrescriptionStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    paid = "paid"
    dispensed = "dispensed"

class Prescription(Base):
    __tablename__ = "prescriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id"), index=True)
    status: Mapped[PrescriptionStatus] = mapped_column(
        Enum(PrescriptionStatus, native_enum=False, length=20), default=PrescriptionStatus.pending_payment)
    total_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    encounter = relationship("Encounter", lazy="joined")
    items = relationship("PrescriptionItem", lazy="selectin", cascade="all, delete-orphan")

class PrescriptionItem(Base):
    __tablename__ = "prescription_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"))
    drug_name: Mapped[str] = mapped_column(String(128))
    spec: Mapped[str | None] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    usage: Mapped[str | None] = mapped_column(String(128))

class LabOrderStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    paid = "paid"
    reported = "reported"

class LabOrder(Base):
    __tablename__ = "lab_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id"), index=True)
    item_name: Mapped[str] = mapped_column(String(128))
    fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[LabOrderStatus] = mapped_column(
        Enum(LabOrderStatus, native_enum=False, length=20), default=LabOrderStatus.pending_payment)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    encounter = relationship("Encounter", lazy="joined")

class AIStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"

class LabReport(Base):
    __tablename__ = "lab_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    lab_order_id: Mapped[int] = mapped_column(ForeignKey("lab_orders.id"), unique=True)
    raw_text: Mapped[str] = mapped_column(Text)
    items_json: Mapped[dict | list | None] = mapped_column(JSON)
    ai_status: Mapped[AIStatus] = mapped_column(Enum(AIStatus, native_enum=False, length=12), default=AIStatus.pending)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_degraded: Mapped[bool] = mapped_column(default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    lab_order = relationship("LabOrder", lazy="joined")

class PaymentKind(str, enum.Enum):
    prescription = "prescription"
    lab = "lab"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[PaymentKind] = mapped_column(Enum(PaymentKind, native_enum=False, length=16))
    ref_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=8), default=PaymentStatus.pending)
    cashier_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    patient = relationship("User", foreign_keys=[patient_id], lazy="joined")

class DispenseRecord(Base):
    __tablename__ = "dispense_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"), unique=True)
    pharmacist_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
