import enum
from datetime import date, datetime
from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str | None] = mapped_column(Text)

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    title: Mapped[str] = mapped_column(String(32), default="主治医师")
    bio: Mapped[str | None] = mapped_column(Text)
    user = relationship("User", lazy="joined")
    department = relationship("Department", lazy="joined")

class Slot(str, enum.Enum):
    am = "am"
    pm = "pm"

class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (UniqueConstraint("doctor_id", "work_date", "slot"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctor_profiles.id"))
    work_date: Mapped[date] = mapped_column(Date, index=True)
    slot: Mapped[Slot] = mapped_column(Enum(Slot, native_enum=False, length=8))
    capacity: Mapped[int] = mapped_column(Integer, default=20)
    booked: Mapped[int] = mapped_column(Integer, default=0)
    doctor = relationship("DoctorProfile", lazy="joined")

class AppointmentStatus(str, enum.Enum):
    booked = "booked"
    cancelled = "cancelled"
    completed = "completed"

class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"))
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, native_enum=False, length=16), default=AppointmentStatus.booked)
    triage_session_id: Mapped[int | None] = mapped_column(ForeignKey("triage_sessions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    patient = relationship("User", lazy="joined")
    schedule = relationship("Schedule", lazy="joined")
