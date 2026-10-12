"""Patient health profile schemas. Closed lists are validated against app/shared/health_options.py."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.shared.health_options import CHRONIC_CONDITIONS, FAMILY_HISTORY

ChronicCondition = Literal[
    "diabetes", "hypertension", "asthma_copd", "heart_disease", "kidney_disease", "liver_disease",
    "thyroid_disorder", "tuberculosis", "epilepsy", "cancer", "skin_disease", "arthritis",
    "mental_health", "anaemia",
]
FamilyCondition = Literal[
    "diabetes", "hypertension", "heart_disease", "tuberculosis", "cancer", "asthma", "mental_illness",
    "epilepsy", "thyroid_disorder",
]
HabitStatus = Literal["never", "former", "current"]
DietType = Literal["vegetarian", "non_vegetarian", "mixed"]
AllergyType = Literal["drug", "food", "herb", "dust_pollen", "skin_contact", "insect", "other"]
AllergySeverity = Literal["mild", "moderate", "severe"]

assert set(ChronicCondition.__args__) == set(CHRONIC_CONDITIONS)  # type: ignore[attr-defined]
assert set(FamilyCondition.__args__) == set(FAMILY_HISTORY)  # type: ignore[attr-defined]


class AllergyEntry(BaseModel):
    type: AllergyType
    substance: str = Field(..., min_length=1, max_length=100, description="What the patient reacts to")
    severity: AllergySeverity | None = None

    @field_validator("substance")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name what the patient is allergic to.")
        return value


class HealthProfileUpdate(BaseModel):
    """The whole profile is sent each time (replace, not patch): the form always shows all of it."""

    chronic_conditions: list[ChronicCondition] = Field(default_factory=list, max_length=len(CHRONIC_CONDITIONS))
    allergies: list[AllergyEntry] = Field(default_factory=list, max_length=30)
    family_history: list[FamilyCondition] = Field(default_factory=list, max_length=len(FAMILY_HISTORY))

    smoking: HabitStatus | None = None
    alcohol: HabitStatus | None = None
    betel_tobacco: HabitStatus | None = None
    diet_type: DietType | None = None

    pregnant: bool = False
    lmp_date: date | None = None
    breastfeeding: bool = False

    on_allopathic_medicines: bool = False
    on_blood_thinners: bool = False
    recent_surgery: bool = False
    current_medicines_note: str | None = Field(default=None, max_length=1000)
    past_surgeries_note: str | None = Field(default=None, max_length=1000)

    @field_validator("chronic_conditions", "family_history")
    @classmethod
    def _unique(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def _check(self):
        if self.lmp_date is not None:
            if not self.pregnant:
                raise ValueError("A last menstrual period date is only kept for a pregnant patient.")
            if self.lmp_date > date.today():
                raise ValueError("The last menstrual period cannot be in the future.")
        return self


class HealthProfileResponse(HealthProfileUpdate):
    model_config = ConfigDict(from_attributes=True)

    patient_id: str
    # False until a profile has been saved: the fields are then all empty defaults
    exists: bool
    updated_at: datetime | None = None
    # Warnings to show on the patient and prescription screens (codes from SAFETY_FLAGS)
    safety_flags: list[str] = Field(default_factory=list)


class HealthOptionsResponse(BaseModel):
    """Every closed list, so the frontend never keeps its own copy of the codes."""

    chronic_conditions: list[str]
    allergy_types: list[str]
    allergy_severities: list[str]
    family_history: list[str]
    habit_statuses: list[str]
    diet_types: list[str]
    red_flags: list[str]
    referral_urgencies: list[str]
    blood_sugar_types: list[str]
    safety_flags: list[str]
