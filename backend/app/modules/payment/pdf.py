"""HTML for the printable invoice (rendered to PDF by app/core/pdf.py)."""

from __future__ import annotations

from decimal import Decimal

from app.core.pdf import document, esc, label, multiline

STATUS_LABELS = {
    "paid": ("PAID", "পরিশোধিত"),
    "pending": ("PENDING", "বাকি"),
    "refunded": ("REFUNDED", "ফেরত"),
    "failed": ("FAILED", "ব্যর্থ"),
    "cancelled": ("CANCELLED", "বাতিল"),
}


METHOD_LABELS = {"bkash": "bKash", "nagad": "Nagad", "rocket": "Rocket", "cash": "Cash", "card": "Card"}


def money(amount: object, currency: str) -> str:
    return f"{currency} {Decimal(str(amount)):,.2f}"


def build_invoice_html(*, invoice, payment, patient, tenant) -> str:
    clinic_name = tenant.clinic_name or tenant.name
    address = ", ".join(
        part
        for part in (tenant.address_line_1, tenant.address_line_2, tenant.landmark, tenant.postal_code)
        if part
    ) or (tenant.clinic_address or "")
    contact = " · ".join(
        part for part in (tenant.clinic_phone or tenant.phone, tenant.clinic_email) if part
    )

    created = invoice.created_at.strftime("%d %b %Y") if invoice.created_at else ""
    due = invoice.due_date.strftime("%d %b %Y") if invoice.due_date else "—"
    paid_on = payment.payment_date.strftime("%d %b %Y") if payment.payment_date else ""

    status_en, status_bn = STATUS_LABELS.get(payment.status, (payment.status.upper(), ""))
    stamp_class = "stamp ok" if payment.status == "paid" else "stamp"
    stamp = f"<div class='{stamp_class}'>{esc(status_en)}</div>" if payment.status != "pending" else ""

    description = payment.description or "Consultation / চিকিৎসা সেবা"
    total = money(payment.amount, payment.currency)

    def row(k_html: str, v: str) -> str:
        if not v.strip():
            return ""
        return f"<tr><td class='k'>{k_html}</td><td>{v}</td></tr>"

    left = "".join(
        [
            row(label("Billed to", "প্রাপক"), f"<strong>{esc(patient.full_name)}</strong>"),
            row(label("Phone", "ফোন"), esc(patient.phone)),
            row(label("Address", "ঠিকানা"), esc(patient.address)),
        ]
    )
    right = "".join(
        [
            row(label("Invoice No.", "ইনভয়েস নং"), f"<strong>{esc(invoice.invoice_number)}</strong>"),
            row(label("Date", "তারিখ"), esc(created)),
            row(label("Due", "মেয়াদ"), esc(due)),
        ]
    )

    pay_details = [
        row(label("Method", "পদ্ধতি"), esc(METHOD_LABELS.get(payment.payment_method, (payment.payment_method or "").replace("_", " ").title()))),
        row(label("Payment date", "পরিশোধের তারিখ"), esc(paid_on)),
        row(label("Status", "অবস্থা"), f"{esc(status_en)} <span class='bn'>/ {esc(status_bn)}</span>"),
    ]
    if payment.transaction_id:
        pay_details.append(row(label("Transaction ID", "ট্রানজেকশন আইডি"), esc(payment.transaction_id)))

    body = (
        "<div class='letterhead'>"
        f"<div class='clinic'><h1>{esc(clinic_name)}</h1><p>{esc(address)}</p>"
        f"<p class='muted'>{esc(contact)}</p></div>"
        f"<div class='doctor'><strong>{label('INVOICE', 'ইনভয়েস')}</strong></div></div>"
        "<table class='meta'><tr>"
        f"<td style='width:55%'><table class='meta'>{left}</table></td>"
        f"<td><table class='meta'>{right}</table></td></tr></table>"
        "<h2>" + label("Details", "বিবরণ") + "</h2>"
        "<table><thead><tr>"
        f"<th>{label('Description', 'বিবরণ')}</th><th class='num'>{label('Amount', 'টাকা')}</th>"
        f"</tr></thead><tbody><tr><td>{multiline(description)}</td>"
        f"<td class='num'>{esc(total)}</td></tr></tbody></table>"
        "<table class='totals' style='margin-top:6pt'>"
        f"<tr class='grand'><td>{label('Total', 'মোট')}</td><td class='num'>{esc(total)}</td></tr></table>"
        "<h2>" + label("Payment", "পরিশোধ") + "</h2>"
        f"<table class='meta'>{''.join(pay_details)}</table>"
        + stamp
    )
    return document(f"Invoice {invoice.invoice_number}", body)
