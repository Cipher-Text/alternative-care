"""Unani case-taking fields (draft v1, pending review by practising Unani doctors).

Generated once from docs/planning/health-history-field-review-2026-10.md (rows U1-U23); edit by hand from here.
Keep the labels in frontend/src/messages/{en,bn}/caseTaking.json in step: tests/integration/test_case_taking.py
fails if a key, group or option has no label.

Taken once (patient): the person's mizaj. Taken at each visit: the disease's mizaj and the humours, the
examination (nabz, baul, baraz and so on), the six essential factors, and the treatment by regimen, diet and drug.
Many terms here are marked "check term" in the review document: expect edits from the reviewing hakim.
"""

from app.shared.case_taking import Field, System

FIELDS = (
    Field(key="mizaj", group="constitution", scope="patient", type="one", options=('damvi', 'balghami', 'safravi', 'saudavi')),
    Field(key="disease_mizaj", group="diagnosis", scope="visit", type="one", options=('hot_dry', 'hot_moist', 'cold_dry', 'cold_moist')),
    Field(key="akhlat_affected", group="diagnosis", scope="visit", type="many", options=('dam', 'balgham', 'safra', 'sauda')),
    Field(key="nabz_rate", group="examination", scope="visit", type="quantity", units=('per_minute',)),
    Field(key="nabz_character", group="examination", scope="visit", type="many", options=('strong', 'weak', 'fast', 'slow', 'full', 'empty', 'hard', 'soft', 'irregular')),
    Field(key="baul_colour", group="examination", scope="visit", type="one", options=('pale', 'straw', 'yellow', 'dark')),
    Field(key="baul_clarity", group="examination", scope="visit", type="one", options=('clear', 'turbid', 'sediment')),
    Field(key="baraz", group="examination", scope="visit", type="one", options=('normal', 'hard', 'loose', 'mucous', 'pale', 'dark')),
    Field(key="skin_complexion", group="examination", scope="visit", type="one", options=('pale', 'ruddy', 'yellowish', 'dusky')),
    Field(key="tongue", group="examination", scope="visit", type="one", options=('clean', 'white', 'yellow', 'dry')),
    Field(key="lams_notes", group="examination", scope="visit", type="text"),
    Field(key="hawa_e_muhit", group="six_factors", scope="visit", type="one", options=('normal', 'excess', 'deficient', 'abnormal')),
    Field(key="makool_mashroob", group="six_factors", scope="visit", type="one", options=('normal', 'excess', 'deficient', 'abnormal')),
    Field(key="harkat_badni", group="six_factors", scope="visit", type="one", options=('normal', 'excess', 'deficient', 'abnormal')),
    Field(key="harkat_nafsani", group="six_factors", scope="visit", type="one", options=('normal', 'excess', 'deficient', 'abnormal')),
    Field(key="naum_yaqza", group="six_factors", scope="visit", type="one", options=('normal', 'excess', 'deficient', 'abnormal')),
    Field(key="ehtebas_istifragh", group="six_factors", scope="visit", type="one", options=('normal', 'excess', 'deficient', 'abnormal')),
    Field(key="ilaj_tadbeer", group="treatment", scope="visit", type="many", options=('hijama', 'fasd', 'dalk', 'hammam', 'riyazat', 'taleeq', 'ishal', 'qai', 'huqna', 'idrar')),
    Field(key="ilaj_ghiza", group="treatment", scope="visit", type="text", max_length=1000),
    Field(key="ilaj_dawa_drug", group="treatment", scope="visit", type="text"),
    Field(key="drug_type", group="treatment", scope="visit", type="one", options=('mufrad', 'murakkab')),
    Field(key="drug_form", group="treatment", scope="visit", type="one", options=('safoof', 'joshanda', 'sharbat', 'majoon', 'qurs', 'marham', 'roghan', 'arq', 'khamira')),
    Field(key="drug_mizaj_degree", group="treatment", scope="visit", type="text"),
)

UNANI = System(
    key="unani",
    fields=FIELDS,
    groups=(
        ("constitution", "patient"),
        ("diagnosis", "visit"),
        ("examination", "visit"),
        ("six_factors", "visit"),
        ("treatment", "visit"),
    ),
)
