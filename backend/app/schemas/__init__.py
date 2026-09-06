from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    full_name: str = Field(min_length=1, max_length=32)
    phone: str | None = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(ORMModel):
    id: int; username: str; full_name: str; role: str; phone: str | None = None

class DepartmentOut(ORMModel):
    id: int; name: str; description: str | None = None

class DoctorOut(ORMModel):
    id: int; title: str; bio: str | None = None; full_name: str; department_id: int; department_name: str

class ScheduleOut(ORMModel):
    id: int; work_date: date; slot: str; capacity: int; booked: int

class TriageMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

class TriageResult(BaseModel):
    department: str; urgency: str = Field(description="low/medium/high/emergency"); advice: str; degraded: bool = False

class TriageSessionOut(ORMModel):
    id: int; status: str; result_json: dict | None = None; created_at: datetime

class AppointmentIn(BaseModel):
    schedule_id: int; triage_session_id: int | None = None

class AppointmentOut(ORMModel):
    id: int; status: str; created_at: datetime; patient_name: str; doctor_name: str; department_name: str; work_date: date; slot: str

class EncounterIn(BaseModel):
    appointment_id: int

class EncounterUpdate(BaseModel):
    chief_complaint: str | None = None; diagnosis: str | None = None; plan: str | None = None; close: bool = False

class EncounterOut(ORMModel):
    id: int; appointment_id: int; patient_id: int; patient_name: str; chief_complaint: str | None; diagnosis: str | None; plan: str | None; status: str; created_at: datetime

class PrescriptionItemIn(BaseModel):
    drug_name: str; spec: str | None = None; quantity: int = Field(ge=1, default=1); price: Decimal = Field(ge=0); usage: str | None = None

class PrescriptionIn(BaseModel):
    items: list[PrescriptionItemIn] = Field(min_length=1)

class PrescriptionItemOut(ORMModel):
    id: int; drug_name: str; spec: str | None; quantity: int; price: Decimal; usage: str | None

class PrescriptionOut(ORMModel):
    id: int; encounter_id: int; status: str; total_fee: Decimal; created_at: datetime; items: list[PrescriptionItemOut] = []; patient_name: str | None = None

class LabOrderIn(BaseModel):
    item_name: str; fee: Decimal = Field(ge=0)

class LabOrderOut(ORMModel):
    id: int; encounter_id: int; item_name: str; fee: Decimal; status: str; created_at: datetime; patient_name: str | None = None

class LabReportIn(BaseModel):
    raw_text: str = Field(min_length=1); items_json: list[dict] | None = None

class LabReportOut(ORMModel):
    id: int; lab_order_id: int; item_name: str | None = None; raw_text: str; items_json: list | dict | None; ai_status: str; ai_summary: str | None; ai_degraded: bool; created_at: datetime

class PaymentOut(ORMModel):
    id: int; kind: str; ref_id: int; amount: Decimal; status: str; patient_name: str; created_at: datetime

class KbDocumentIn(BaseModel):
    title: str = Field(min_length=1, max_length=200); source: str | None = None; content: str = Field(min_length=10)

class KbDocumentOut(ORMModel):
    id: int; title: str; source: str | None; status: str; error: str | None = None; chunk_count: int; created_at: datetime

class LlmLogOut(ORMModel):
    id: int; user_id: int | None; scene: str; model: str; prompt_tokens: int; completion_tokens: int; latency_ms: int; status: str; error: str | None; created_at: datetime

class StatsOut(BaseModel):
    total_calls: int; ok_calls: int; error_calls: int; fallback_calls: int; total_tokens: int; avg_latency_ms: float; today_calls: int; scene_breakdown: dict[str, int]
