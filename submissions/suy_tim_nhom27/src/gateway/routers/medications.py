"""Database-backed medication reads and manual synthetic medication entry."""
from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from psycopg import Error as PsycopgError

from ..authorization import Actor, get_current_actor, require_case_access, require_role
from ..database import staff_connection


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MedicationCreate(ApiModel):
    expected_revision: int = Field(ge=1)
    ingredient_code: str = Field(pattern=r"^[a-z][a-z0-9_]{1,59}$")
    dose: float = Field(gt=0, allow_inf_nan=False)
    dose_unit: Literal["mg", "mcg", "g", "mL"]
    route: Literal["oral", "iv", "other"]
    frequency_per_day: int = Field(ge=1, le=24)
    kind: Literal["current", "proposed"]
    starts_on: date | None = None
    ends_on: date | None = None
    instructions: str = Field(default="", max_length=2000)

    @field_validator("instructions")
    @classmethod
    def normalize_instructions(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def valid_date_range(self) -> "MedicationCreate":
        if self.starts_on is not None and self.ends_on is not None and self.ends_on < self.starts_on:
            raise ValueError("ends_on must not precede starts_on")
        return self


class MedicationOut(ApiModel):
    id: UUID
    encounter_id: UUID
    ingredient_code: str
    dose: float
    dose_unit: Literal["mg", "mcg", "g", "mL"]
    route: Literal["oral", "iv", "other"]
    frequency_per_day: int
    kind: Literal["current", "proposed"]
    starts_on: date
    ends_on: date | None
    instructions: str


def _database_error(error: PsycopgError) -> HTTPException:
    """Return safe errors without forwarding database diagnostics to callers."""
    state = getattr(error, "sqlstate", None)
    if state == "23505":
        return HTTPException(status_code=409, detail="Thuốc xung đột với dữ liệu hiện tại")
    if state in {"23502", "23503", "23514", "22003", "22007", "22P02"}:
        return HTTPException(status_code=422, detail="Dữ liệu thuốc không hợp lệ")
    if state and state.startswith("08"):
        return HTTPException(status_code=503, detail="Cơ sở dữ liệu demo tạm thời không sẵn sàng")
    return HTTPException(status_code=500, detail="Không thể hoàn tất thao tác với dữ liệu demo")


def build_medications_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/api/v1/encounters/{encounter_id}/medications",
        response_model=list[MedicationOut],
        tags=["Clinical data"],
    )
    def list_medications(
        encounter_id: UUID,
        request: Request,
        actor: Actor = Depends(get_current_actor),
    ) -> list[MedicationOut]:
        require_role(actor, {"doctor", "pharmacist"})
        scope = "clinical" if actor.role == "doctor" else "medsafety"
        try:
            with staff_connection(request, actor) as conn:
                encounter = conn.execute(
                    "SELECT id, case_id FROM encounter WHERE id = %s",
                    (encounter_id,),
                ).fetchone()
                if encounter is None:
                    raise HTTPException(status_code=404, detail="Không tìm thấy lượt khám")
                require_case_access(conn, actor, encounter["case_id"], {scope})
                rows = conn.execute(
                    """
                    SELECT id, encounter_id, ingredient_code, dose, dose_unit, route,
                           frequency_per_day, kind, starts_on, ends_on, instructions
                    FROM medication
                    WHERE encounter_id = %s
                    ORDER BY created_at, id
                    """,
                    (encounter_id,),
                ).fetchall()
                return [MedicationOut(**row) for row in rows]
        except HTTPException:
            raise
        except PsycopgError as error:
            raise _database_error(error) from None

    @router.post(
        "/api/v1/encounters/{encounter_id}/medications",
        response_model=MedicationOut,
        status_code=201,
        tags=["Clinical data"],
    )
    def create_medication(
        encounter_id: UUID,
        body: MedicationCreate,
        request: Request,
        actor: Actor = Depends(get_current_actor),
    ) -> MedicationOut:
        require_role(actor, {"doctor"})
        try:
            with staff_connection(request, actor) as conn:
                encounter = conn.execute(
                    """
                    SELECT e.id, e.case_id, e.status, c.revision
                    FROM encounter AS e
                    JOIN patient_case AS c ON c.id = e.case_id
                    WHERE e.id = %s
                    FOR UPDATE OF c
                    """,
                    (encounter_id,),
                ).fetchone()
                if encounter is None:
                    raise HTTPException(status_code=404, detail="Không tìm thấy lượt khám")
                require_case_access(conn, actor, encounter["case_id"], {"clinical"})
                if encounter["status"] == "cancelled":
                    raise HTTPException(status_code=409, detail="Không thể cập nhật lượt khám đã hủy")
                if encounter["revision"] != body.expected_revision:
                    raise HTTPException(status_code=409, detail="Ca đã thay đổi; hãy tải lại dữ liệu")

                # This creates only a manually recorded medication row. In particular,
                # it does not create/confirm a prescription, schedule, or mock result.
                row = conn.execute(
                    """
                    INSERT INTO medication(
                        encounter_id, ingredient_code, dose, dose_unit, route,
                        frequency_per_day, kind, starts_on, ends_on, instructions, recorded_by
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        COALESCE(%s::date, CURRENT_DATE), %s, %s, %s
                    )
                    RETURNING id, encounter_id, ingredient_code, dose, dose_unit, route,
                              frequency_per_day, kind, starts_on, ends_on, instructions
                    """,
                    (
                        encounter_id,
                        body.ingredient_code,
                        body.dose,
                        body.dose_unit,
                        body.route,
                        body.frequency_per_day,
                        body.kind,
                        body.starts_on,
                        body.ends_on,
                        body.instructions,
                        actor.user_id,
                    ),
                ).fetchone()
                # The database's medication_revision trigger increments case revision.
                return MedicationOut(**row)
        except HTTPException:
            raise
        except PsycopgError as error:
            raise _database_error(error) from None

    return router
