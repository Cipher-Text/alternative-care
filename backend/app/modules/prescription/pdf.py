"""HTML for the printable prescription (rendered to PDF by app/core/pdf.py).

Pure functions over already-loaded rows so they are trivially testable. Patient-facing content
only: the doctor's internal notes (`doctors_notes`) are deliberately NOT printed.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from app.core.pdf import document, esc, label, multiline

GENDER_LABELS = {
    "male": ("Male", "পুরুষ"),
    "female": ("Female", "মহিলা"),
    "other": ("Other", "অন্যান্য"),
}


def age_text(dob: date | None, today: date | None = None) -> str:
    """'34 y', '8 mo' for infants, '' when unknown."""
    if dob is None:
        return ""
    today = today or date.today()
    months = (today.year - dob.year) * 12 + (today.month - dob.month) - (today.day < dob.day)
    if months < 0:
        return ""
    if months < 24:
        return f"{months} mo"
    return f"{months // 12} y"


def _letterhead(tenant, doctor, degrees: Iterable) -> str:
    clinic_name = tenant.clinic_name or tenant.name
    address = ", ".join(
        part
        for part in (
            tenant.address_line_1,
            tenant.address_line_2,
            tenant.landmark,
            tenant.postal_code,
        )
        if part
    ) or (tenant.clinic_address or "")
    contact = " · ".join(
        part for part in (tenant.clinic_phone or tenant.phone, tenant.clinic_email) if part
    )
    degree_lines = "".join(
        f"<p class='muted'>{esc(d.degree_name)}"
        f"{', ' + esc(d.institution_name) if d.institution_name else ''}</p>"
        for d in degrees
    )
    registration = " ".join(
        part for part in (tenant.registration_body, tenant.registration_number) if part
    ) or (tenant.license_number or "")
    return (
        "<div class='letterhead'>"
        f"<div class='clinic'><h1>{esc(clinic_name)}</h1>"
        f"<p>{esc(address)}</p><p class='muted'>{esc(contact)}</p></div>"
        f"<div class='doctor'><strong>{esc(doctor.full_name)}</strong>{degree_lines}"
        f"{'<p>' + esc(registration) + '</p>' if registration else ''}</div></div>"
    )


def _meta_row(k_html: str, v: str) -> str:
    """A label/value row; rows with no value are omitted so the printout stays tidy."""
    if not v.strip():
        return ""
    return f"<tr><td class='k'>{k_html}</td><td>{v}</td></tr>"


def build_prescription_html(
    *,
    prescription,
    patient,
    doctor,
    tenant,
    degrees: Iterable,
    medicines_by_id: dict,
) -> str:
    voided = prescription.status == "voided"
    created: datetime | None = prescription.created_at
    date_text = created.strftime("%d %b %Y") if created else ""
    rx_no = prescription.id[:8].upper()

    gender = GENDER_LABELS.get((patient.gender or "").lower())
    gender_text = f"{gender[0]} / {gender[1]}" if gender else ""
    age = age_text(patient.date_of_birth)
    age_gender = " · ".join(p for p in (age, gender_text) if p)

    left = "".join(
        [
            _meta_row(label("Patient", "রোগী"), f"<strong>{esc(patient.full_name)}</strong>"),
            _meta_row(label("Age / Sex", "বয়স / লিঙ্গ"), esc(age_gender)),
            _meta_row(label("Phone", "ফোন"), esc(patient.phone)),
        ]
    )
    right = "".join(
        [
            _meta_row(label("Date", "তারিখ"), esc(date_text)),
            _meta_row(label("Rx No.", "নম্বর"), esc(rx_no)),
        ]
    )

    rows = []
    for index, item in enumerate(prescription.items, start=1):
        medicine = medicines_by_id.get(item.medicine_id)
        if medicine is not None:
            name = esc(medicine.name_en) + (
                f" <span class='muted'>{esc(medicine.potency)}</span>" if medicine.potency else ""
            )
            if medicine.name_bn:
                name += f"<br><span class='bn'>{esc(medicine.name_bn)}</span>"
        else:
            name = esc(item.medicine_name or "—")
        quantity = ""
        if item.quantity is not None:
            quantity = f"{float(item.quantity):g}"
        rows.append(
            "<tr>"
            f"<td>{index}</td><td><strong>{name}</strong></td>"
            f"<td>{esc(item.dosage)}</td><td>{esc(item.frequency)}</td>"
            f"<td>{esc(item.duration)}</td><td class='num'>{esc(quantity)}</td>"
            f"<td>{multiline(item.instructions)}</td></tr>"
        )
    table = (
        "<table><thead><tr>"
        "<th>#</th>"
        f"<th>{label('Medicine', 'ঔষধ')}</th><th>{label('Dose', 'মাত্রা')}</th>"
        f"<th>{label('Frequency', 'নিয়ম')}</th><th>{label('Duration', 'মেয়াদ')}</th>"
        f"<th class='num'>{label('Qty', 'পরিমাণ')}</th><th>{label('Instructions', 'নির্দেশনা')}</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )

    sections = []
    if prescription.diagnosis:
        sections.append(
            f"<h2>{label('Diagnosis', 'রোগ নির্ণয়')}</h2><p>{multiline(prescription.diagnosis)}</p>"
        )
    sections.append(f"<div class='rx'>℞</div>{table}")
    if prescription.advice:
        sections.append(
            f"<h2>{label('Advice', 'পরামর্শ')}</h2><p>{multiline(prescription.advice)}</p>"
        )

    body = (
        _letterhead(tenant, doctor, degrees)
        + "<table class='meta'><tr>"
        f"<td style='width:55%'><table class='meta'>{left}</table></td>"
        f"<td><table class='meta'>{right}</table></td></tr></table>"
        + "".join(sections)
        + f"<div class='signature'><div>{label('Doctor’s signature', 'চিকিৎসকের স্বাক্ষর')}</div></div>"
        + ("<div class='stamp'>VOID</div>" if voided else "")
    )
    return document(f"Prescription {rx_no}", body)
