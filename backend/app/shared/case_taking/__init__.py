"""System-specific case-taking (homeopathy now; Ayurveda and Unani use the same machinery).

A system is a list of `Field` definitions. Each field belongs to a group and a scope:
- "patient": taken once and kept up to date (constitution, generals, history) -> `patient_case_profiles`
- "visit":   taken at each visit (the complaint in detail, the prescription, the response) -> `visit_assessments`

Answers are stored as JSON under fixed keys with closed option codes, validated here. The frontend renders
the forms from `definitions()` and takes the labels (English and Bengali) from its translation files, so
adding or changing a field means editing the registry file and the labels, never a database migration.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

FieldType = Literal["one", "many", "text", "quantity", "table"]
Scope = Literal["patient", "visit"]
SCHEMA_VERSION = 1

MAX_TEXT = 1000
MAX_TABLE_ROWS = 20


@dataclass(frozen=True)
class Field:
    key: str
    group: str
    scope: Scope
    type: FieldType
    options: tuple[str, ...] = ()  # one / many
    units: tuple[str, ...] = ()  # quantity
    columns: tuple["Field", ...] = ()  # table
    max_length: int = 500  # text


@dataclass(frozen=True)
class System:
    key: str
    fields: tuple[Field, ...]
    groups: tuple[tuple[str, Scope], ...] = field(default=())

    def scoped(self, scope: Scope) -> dict[str, Field]:
        return {f.key: f for f in self.fields if f.scope == scope}


class CaseValidationError(ValueError):
    """`errors` maps a field key to a short English reason; the API returns it as a 422."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("; ".join(f"{k}: {v}" for k, v in errors.items()))
        self.errors = errors


def _clean_value(f: Field, value: Any) -> Any:
    """Validated value, or None when it is empty (empty answers are not stored). Raises ValueError."""
    if value is None or value == "" or value == [] or value == {}:
        return None
    if f.type == "text":
        if not isinstance(value, str):
            raise ValueError("must be text")
        value = value.strip()
        if len(value) > min(f.max_length, MAX_TEXT):
            raise ValueError(f"must be at most {min(f.max_length, MAX_TEXT)} characters")
        return value or None
    if f.type == "one":
        if value not in f.options:
            raise ValueError("is not one of the allowed choices")
        return value
    if f.type == "many":
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ValueError("must be a list of choices")
        bad = [v for v in value if v not in f.options]
        if bad:
            raise ValueError(f"has unknown choices: {', '.join(bad)}")
        return list(dict.fromkeys(value)) or None
    if f.type == "quantity":
        if not isinstance(value, dict) or set(value) - {"value", "unit"}:
            raise ValueError("must be a number with a unit")
        number, unit = value.get("value"), value.get("unit")
        if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= 1000:
            raise ValueError("needs a whole number from 1 to 1000")
        if unit not in f.units:
            raise ValueError("needs a valid unit")
        return {"value": number, "unit": unit}
    if f.type == "table":
        if not isinstance(value, list) or len(value) > MAX_TABLE_ROWS:
            raise ValueError(f"must be a list of at most {MAX_TABLE_ROWS} rows")
        rows = []
        for row in value:
            if not isinstance(row, dict) or set(row) - {c.key for c in f.columns}:
                raise ValueError("has a row with unknown columns")
            cleaned = {}
            for column in f.columns:
                try:
                    v = _clean_value(column, row.get(column.key))
                except ValueError as exc:
                    raise ValueError(f"{column.key} {exc}") from None
                if v is not None:
                    cleaned[column.key] = v
            if cleaned:
                rows.append(cleaned)
        return rows or None
    raise ValueError("unsupported field type")  # pragma: no cover


def validate(system: System, scope: Scope, data: dict[str, Any]) -> dict[str, Any]:
    """The cleaned answers for `scope`: unknown keys and bad values are refused, empty ones dropped."""
    fields = system.scoped(scope)
    errors: dict[str, str] = {}
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        f = fields.get(key)
        if f is None:
            errors[key] = "is not a field of this form"
            continue
        try:
            v = _clean_value(f, value)
        except ValueError as exc:
            errors[key] = str(exc)
            continue
        if v is not None:
            cleaned[key] = v
    if errors:
        raise CaseValidationError(errors)
    return cleaned


def definitions(system: System) -> dict[str, Any]:
    """What the frontend needs to draw the forms (no labels: those are translations)."""

    def one(f: Field) -> dict[str, Any]:
        out: dict[str, Any] = {"key": f.key, "group": f.group, "scope": f.scope, "type": f.type}
        if f.options:
            out["options"] = list(f.options)
        if f.units:
            out["units"] = list(f.units)
        if f.columns:
            out["columns"] = [one(c) for c in f.columns]
        if f.type == "text":
            out["max_length"] = min(f.max_length, MAX_TEXT)
        return out

    return {
        "system": system.key,
        "schema_version": SCHEMA_VERSION,
        "groups": [{"key": g, "scope": s} for g, s in system.groups],
        "fields": [one(f) for f in system.fields],
    }
