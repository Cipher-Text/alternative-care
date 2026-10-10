"""The printable documents' HTML (pure functions — no database, no PDF engine needed)."""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.core.pdf import esc, multiline
from app.modules.payment.pdf import build_invoice_html, money
from app.modules.prescription.pdf import age_text, build_prescription_html


def _tenant(**overrides):
    base = dict(
        name="Dr. Abdur Rahman",
        clinic_name="Dhanmondi Homeopathy Center",
        clinic_address=None,
        address_line_1="House 12, Road 5",
        address_line_2="Dhanmondi",
        landmark=None,
        postal_code="1205",
        clinic_phone="+8801712345678",
        phone=None,
        clinic_email="clinic@example.com",
        registration_body="BMDC",
        registration_number="A-12345",
        license_number=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _rx(status="issued", **overrides):
    item = SimpleNamespace(
        medicine_id=None,
        medicine_name="Belladonna 30C",
        dosage="5 drops",
        frequency="3 times daily",
        duration="7 days",
        quantity=Decimal("1"),
        instructions="Before meals\nWith water",
    )
    base = dict(
        id="a8c105f7-5372-472f-94f6-1bd3f18584f3",
        status=status,
        diagnosis="Acute fever",
        doctors_notes="PRIVATE internal note",
        advice="বিশ্রাম নিন এবং প্রচুর পানি পান করুন।",
        created_at=datetime(2026, 10, 10, tzinfo=timezone.utc),
        items=[item],
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _html(rx=None, patient=None, tenant=None, degrees=()):
    return build_prescription_html(
        prescription=rx or _rx(),
        patient=patient
        or SimpleNamespace(
            full_name="রহিম উদ্দিন", gender="male", date_of_birth=date(1990, 1, 15), phone="01700000000"
        ),
        doctor=SimpleNamespace(full_name="Dr. Abdur Rahman"),
        tenant=tenant or _tenant(),
        degrees=degrees,
        medicines_by_id={},
    )


def test_prescription_contains_the_patient_facing_content():
    html = _html(
        degrees=[SimpleNamespace(degree_name="DHMS", institution_name="Dhaka Homoeopathic College")]
    )
    for expected in (
        "Dhanmondi Homeopathy Center",
        "Dr. Abdur Rahman",
        "DHMS, Dhaka Homoeopathic College",
        "BMDC A-12345",
        "রহিম উদ্দিন",
        "Acute fever",
        "Belladonna 30C",
        "5 drops",
        "3 times daily",
        "বিশ্রাম নিন",
        "Doctor’s signature",
        "রোগী",  # bilingual labels
    ):
        assert expected in html, expected


def test_doctors_internal_notes_are_never_printed():
    assert "PRIVATE internal note" not in _html()


def test_voided_prescription_is_stamped_and_issued_one_is_not():
    assert "VOID" in _html(_rx(status="voided"))
    assert "VOID" not in _html(_rx(status="issued"))


def test_user_supplied_text_is_escaped():
    rx = _rx(diagnosis="<script>alert(1)</script>")
    html = _html(rx, patient=SimpleNamespace(
        full_name="<b>Eve</b>", gender=None, date_of_birth=None, phone=None
    ))
    assert "<script>" not in html and "<b>Eve</b>" not in html
    assert "&lt;script&gt;" in html


def test_free_text_line_breaks_are_kept():
    assert "Before meals<br>With water" in _html()
    assert multiline("a\nb") == "a<br>b"
    assert esc(None) == ""


def test_age_text():
    today = date(2026, 10, 10)
    assert age_text(None, today) == ""
    assert age_text(date(2026, 4, 10), today) == "6 mo"
    assert age_text(date(1990, 1, 15), today) == "36 y"
    assert age_text(date(2030, 1, 1), today) == ""


def test_invoice_html_shows_amounts_status_and_number():
    invoice = SimpleNamespace(
        invoice_number="INV-202610-0001",
        created_at=datetime(2026, 10, 10, tzinfo=timezone.utc),
        due_date=date(2026, 10, 24),
    )
    payment = SimpleNamespace(
        amount=Decimal("1500"), currency="BDT", status="paid", payment_method="bkash",
        payment_date=date(2026, 10, 10), description="Consultation", transaction_id="TX123",
    )
    patient = SimpleNamespace(full_name="রহিম উদ্দিন", phone="017", address="Dhaka")
    html = build_invoice_html(invoice=invoice, payment=payment, patient=patient, tenant=_tenant())
    for expected in ("INV-202610-0001", "BDT 1,500.00", "PAID", "bKash", "TX123", "রহিম উদ্দিন", "ইনভয়েস"):
        assert expected in html, expected
    assert money(Decimal("0.5"), "BDT") == "BDT 0.50"
