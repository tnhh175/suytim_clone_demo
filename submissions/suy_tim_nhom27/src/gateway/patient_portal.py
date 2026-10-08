from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from typing import Any, Callable, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from .authorization import Actor, get_current_actor, require_role
from .database import portal_connection


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DoctorOption(_Input):
    doctor_id: UUID
    label: str
    department_code: str
    department_name: str


class AppointmentCreate(_Input):
    doctor_id: UUID
    slot_at: AwareDatetime
    reason: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def nonblank_reason(self):
        if not self.reason.strip():
            raise ValueError("Lý do không được để trống")
        return self


class AppointmentOut(_Input):
    id: UUID
    case_id: UUID
    doctor_id: UUID
    slot_at: AwareDatetime
    reason: str
    status: Literal["requested", "confirmed", "completed", "cancelled"]
    encounter_id: UUID | None
    created_at: AwareDatetime


class MeasurementCreate(_Input):
    observed_at: AwareDatetime
    systolic_bp: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    diastolic_bp: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    heart_rate: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    weight_kg: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    spo2: Decimal | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    temperature_c: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    symptoms: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_measurement(self):
        if all(
            getattr(self, field) is None
            for field in (
                "systolic_bp",
                "diastolic_bp",
                "heart_rate",
                "weight_kg",
                "spo2",
                "temperature_c",
                "symptoms",
            )
        ):
            raise ValueError("Cần nhập ít nhất một chỉ số hoặc triệu chứng")
        if (self.systolic_bp is None) != (self.diastolic_bp is None):
            raise ValueError("Cần nhập đủ huyết áp tâm thu và tâm trương")
        if self.systolic_bp is not None and self.diastolic_bp is not None and self.systolic_bp < self.diastolic_bp:
            raise ValueError("Huyết áp tâm thu phải lớn hơn hoặc bằng tâm trương")
        if self.symptoms is not None and not self.symptoms.strip():
            raise ValueError("Triệu chứng không được để trống")
        return self


class MeasurementOut(MeasurementCreate):
    id: UUID
    case_id: UUID
    recorded_by: UUID
    created_at: AwareDatetime


class PrescriptionOut(_Input):
    prescription_id: UUID
    case_id: UUID
    status: Literal["confirmed", "cancelled"]
    starts_on: date
    ends_on: date | None
    timezone: str
    prescription_instructions: str
    medication_id: UUID
    ingredient: str
    drug_product: str | None
    dose: Decimal
    dose_unit: str
    route: str
    frequency_per_day: int
    medication_starts_on: date
    medication_ends_on: date | None
    instructions: str
    dose_times: list[time]


class ReminderOut(_Input):
    id: UUID
    case_id: UUID
    prescription_id: UUID
    medication_id: UUID
    ingredient: str
    dose: Decimal
    dose_unit: str
    instructions: str
    dose_time: time
    dose_instructions: str
    timezone: str
    scheduled_on: date
    due_at: AwareDatetime
    status: Literal["pending", "taken", "skipped", "cancelled"]
    responded_at: AwareDatetime | None


class ReminderResponse(_Input):
    status: Literal["taken", "skipped"]


class ReminderStatusOut(_Input):
    id: UUID
    status: Literal["taken", "skipped"]
    responded_at: AwareDatetime


def build_patient_portal_router(
    *,
    actor_dependency: Callable[..., Any] = get_current_actor,
    connection_provider: Callable[..., Any] = portal_connection,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/patient", tags=["Patient portal"])

    def patient(actor: Actor) -> None:
        require_role(actor, {"patient"})

    @router.get("/doctors", response_model=list[DoctorOption])
    def doctors(request: Request, actor: Actor = Depends(actor_dependency)):
        patient(actor)
        with connection_provider(request, actor) as conn:
            return conn.execute(
                "SELECT doctor_id, label, department_code, department_name FROM portal_doctors() ORDER BY label"
            ).fetchall()

    @router.get("/appointments", response_model=list[AppointmentOut])
    def list_appointments(request: Request, actor: Actor = Depends(actor_dependency)):
        patient(actor)
        with connection_provider(request, actor) as conn:
            return conn.execute(
                """SELECT id, case_id, doctor_id, slot_at, reason, status, encounter_id, created_at
                     FROM appointment ORDER BY slot_at DESC, id"""
            ).fetchall()

    @router.post("/appointments", response_model=AppointmentOut, status_code=201)
    def request_appointment(
        body: AppointmentCreate,
        request: Request,
        actor: Actor = Depends(actor_dependency),
    ):
        patient(actor)
        with connection_provider(request, actor) as conn:
            case = conn.execute("SELECT portal_case_id() AS case_id").fetchone()
            if case is None or case["case_id"] is None:
                raise HTTPException(status_code=403, detail="Tài khoản chưa được gắn hồ sơ bệnh nhân")
            row = conn.execute(
                """INSERT INTO appointment (case_id, doctor_id, slot_at, reason, requested_by)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING id, case_id, doctor_id, slot_at, reason, status, encounter_id, created_at""",
                (case["case_id"], body.doctor_id, body.slot_at, body.reason.strip(), actor.user_id),
            ).fetchone()
        return row

    @router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
    def cancel_appointment(
        appointment_id: UUID,
        request: Request,
        actor: Actor = Depends(actor_dependency),
    ):
        patient(actor)
        with connection_provider(request, actor) as conn:
            existing = conn.execute(
                "SELECT status FROM appointment WHERE id = %s",
                (appointment_id,),
            ).fetchone()
            if existing is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn")
            if existing["status"] not in {"requested", "confirmed"}:
                raise HTTPException(status_code=409, detail="Lịch hẹn không còn ở trạng thái có thể hủy")
            row = conn.execute(
                """UPDATE appointment SET status = 'cancelled'
                    WHERE id = %s AND status IN ('requested','confirmed')
                    RETURNING id, case_id, doctor_id, slot_at, reason, status, encounter_id, created_at""",
                (appointment_id,),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=409, detail="Lịch hẹn đã thay đổi; hãy tải lại")
        return row

    @router.get("/measurements", response_model=list[MeasurementOut])
    def list_measurements(request: Request, actor: Actor = Depends(actor_dependency)):
        patient(actor)
        with connection_provider(request, actor) as conn:
            return conn.execute(
                """SELECT id, case_id, recorded_by, observed_at, systolic_bp, diastolic_bp,
                          heart_rate, weight_kg, spo2, temperature_c, symptoms, created_at
                     FROM patient_measurement ORDER BY observed_at DESC, id"""
            ).fetchall()

    @router.post("/measurements", response_model=MeasurementOut, status_code=201)
    def create_measurement(
        body: MeasurementCreate,
        request: Request,
        actor: Actor = Depends(actor_dependency),
    ):
        patient(actor)
        with connection_provider(request, actor) as conn:
            case = conn.execute("SELECT portal_case_id() AS case_id").fetchone()
            if case is None or case["case_id"] is None:
                raise HTTPException(status_code=403, detail="Tài khoản chưa được gắn hồ sơ bệnh nhân")
            row = conn.execute(
                """INSERT INTO patient_measurement
                     (case_id, recorded_by, observed_at, systolic_bp, diastolic_bp,
                      heart_rate, weight_kg, spo2, temperature_c, symptoms)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id, case_id, recorded_by, observed_at, systolic_bp, diastolic_bp,
                             heart_rate, weight_kg, spo2, temperature_c, symptoms, created_at""",
                (
                    case["case_id"],
                    actor.user_id,
                    body.observed_at,
                    body.systolic_bp,
                    body.diastolic_bp,
                    body.heart_rate,
                    body.weight_kg,
                    body.spo2,
                    body.temperature_c,
                    body.symptoms.strip() if body.symptoms is not None else None,
                ),
            ).fetchone()
        return row

    @router.get("/prescriptions", response_model=list[PrescriptionOut])
    def list_prescriptions(request: Request, actor: Actor = Depends(actor_dependency)):
        patient(actor)
        with connection_provider(request, actor) as conn:
            return conn.execute(
                """SELECT prescription_id, case_id, status, starts_on, ends_on, timezone,
                          prescription_instructions, medication_id, ingredient, drug_product,
                          dose, dose_unit, route, frequency_per_day, medication_starts_on,
                          medication_ends_on, instructions, dose_times
                     FROM patient_prescription_view
                    ORDER BY starts_on DESC, prescription_id, medication_id"""
            ).fetchall()

    @router.get("/reminders", response_model=list[ReminderOut])
    def list_reminders(request: Request, actor: Actor = Depends(actor_dependency)):
        patient(actor)
        with connection_provider(request, actor) as conn:
            return conn.execute(
                """SELECT id, case_id, prescription_id, medication_id, ingredient, dose,
                          dose_unit, instructions, dose_time, dose_instructions, timezone,
                          scheduled_on, due_at, status, responded_at
                     FROM patient_reminder_view
                    ORDER BY due_at DESC, id"""
            ).fetchall()

    @router.patch("/reminders/{reminder_id}", response_model=ReminderStatusOut)
    def respond_to_reminder(
        reminder_id: UUID,
        body: ReminderResponse,
        request: Request,
        actor: Actor = Depends(actor_dependency),
    ):
        patient(actor)
        with connection_provider(request, actor) as conn:
            row = conn.execute(
                """UPDATE medication_reminder SET status = %s
                    WHERE id = %s AND status = 'pending'
                    RETURNING id, status, responded_at""",
                (body.status, reminder_id),
            ).fetchone()
            if row is None:
                existing = conn.execute(
                    "SELECT status FROM medication_reminder WHERE id = %s",
                    (reminder_id,),
                ).fetchone()
                if existing is None:
                    raise HTTPException(status_code=404, detail="Không tìm thấy lời nhắc")
                raise HTTPException(status_code=409, detail="Lời nhắc đã được phản hồi")
        return row

    return router


