"""Patient health profile; visit vitals become numbers

Revision ID: f1b7d3a9c5e2
Revises: e8a2c5d7f1b3
Create Date: 2026-10-14 11:00:00

Step 1 of structured health history (homeopathy, Ayurveda and Unani share this core):
- `patient_health_profiles`: one row per patient (chronic conditions, allergies, family history, habits,
  pregnancy, medicine and surgery flags), tenant-isolated like the other clinical tables.
- `visits`: the free-text vitals (temperature, blood_pressure, pulse_rate, weight) become numeric columns,
  plus height, SpO2, respiratory rate, blood sugar, pain score, red flags and referral urgency. Existing
  text values are converted where they parse (Fahrenheit and pounds are converted); the rest is dropped
  with the old columns, as vitals were never entered through the app.
"""
import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1b7d3a9c5e2"
down_revision: Union[str, None] = "e8a2c5d7f1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NUM = re.compile(r"[-+]?\d+(?:\.\d+)?")


def _first_number(text: str | None) -> float | None:
    m = _NUM.search(text or "")
    return float(m.group()) if m else None


def _temperature_c(text: str | None) -> float | None:
    n = _first_number(text)
    if n is None:
        return None
    if re.search(r"f", text or "", re.I) or n > 45:  # Fahrenheit
        n = (n - 32) * 5 / 9
    return round(n, 1) if 30 <= n <= 45 else None


def _weight_kg(text: str | None) -> float | None:
    n = _first_number(text)
    if n is None:
        return None
    if re.search(r"lb|pound", text or "", re.I):
        n = n * 0.45359237
    return round(n, 1) if 0.3 <= n <= 500 else None


def _blood_pressure(text: str | None) -> tuple[int, int] | None:
    m = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", text or "")
    if not m:
        return None
    systolic, diastolic = int(m.group(1)), int(m.group(2))
    return (systolic, diastolic) if 40 <= diastolic < systolic <= 300 else None


def upgrade() -> None:
    op.add_column("visits", sa.Column("temperature_c", sa.Numeric(4, 1), nullable=True))
    op.add_column("visits", sa.Column("pulse_bpm", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("bp_systolic", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("bp_diastolic", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("respiratory_rate", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("spo2_percent", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("weight_kg", sa.Numeric(5, 1), nullable=True))
    op.add_column("visits", sa.Column("height_cm", sa.Numeric(4, 1), nullable=True))
    op.add_column("visits", sa.Column("blood_sugar_mmol", sa.Numeric(4, 1), nullable=True))
    op.add_column("visits", sa.Column("blood_sugar_type", sa.String(15), nullable=True))
    op.add_column("visits", sa.Column("pain_score", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("red_flags", sa.JSON(), nullable=True))
    op.add_column("visits", sa.Column("referral_urgency", sa.String(10), nullable=True))

    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, temperature, blood_pressure, pulse_rate, weight FROM visits")
    ).fetchall()
    for vid, temperature, bp, pulse, weight in rows:
        pressure = _blood_pressure(bp)
        pulse_n = _first_number(pulse)
        bind.execute(
            sa.text(
                "UPDATE visits SET temperature_c = :t, pulse_bpm = :p, bp_systolic = :s, bp_diastolic = :d, "
                "weight_kg = :w WHERE id = :id"
            ),
            {
                "id": vid,
                "t": _temperature_c(temperature),
                "p": int(pulse_n) if pulse_n is not None and 20 <= pulse_n <= 250 else None,
                "s": pressure[0] if pressure else None,
                "d": pressure[1] if pressure else None,
                "w": _weight_kg(weight),
            },
        )
    for column in ("temperature", "blood_pressure", "pulse_rate", "weight"):
        op.drop_column("visits", column)

    op.create_table(
        "patient_health_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("chronic_conditions", sa.JSON(), nullable=False),
        sa.Column("allergies", sa.JSON(), nullable=False),
        sa.Column("family_history", sa.JSON(), nullable=False),
        sa.Column("smoking", sa.String(10), nullable=True),
        sa.Column("alcohol", sa.String(10), nullable=True),
        sa.Column("betel_tobacco", sa.String(10), nullable=True),
        sa.Column("diet_type", sa.String(20), nullable=True),
        sa.Column("pregnant", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("lmp_date", sa.Date(), nullable=True),
        sa.Column("breastfeeding", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("on_allopathic_medicines", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("on_blood_thinners", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("recent_surgery", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("current_medicines_note", sa.Text(), nullable=True),
        sa.Column("past_surgeries_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.UniqueConstraint("patient_id", name="uq_patient_health_profile_patient"),
    )
    op.execute(sa.text("ALTER TABLE patient_health_profiles ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE patient_health_profiles FORCE ROW LEVEL SECURITY"))
    op.execute(
        sa.text(
            "CREATE POLICY tenant_isolation ON patient_health_profiles "
            "USING (tenant_id = current_setting('app.tenant_id', true))"
        )
    )


def downgrade() -> None:
    op.drop_table("patient_health_profiles")
    for column in ("temperature", "blood_pressure", "pulse_rate", "weight"):
        op.add_column("visits", sa.Column(column, sa.String(20), nullable=True))
    for column in (
        "referral_urgency", "red_flags", "pain_score", "blood_sugar_type", "blood_sugar_mmol", "height_cm",
        "weight_kg", "spo2_percent", "respiratory_rate", "bp_diastolic", "bp_systolic", "pulse_bpm", "temperature_c",
    ):
        op.drop_column("visits", column)
