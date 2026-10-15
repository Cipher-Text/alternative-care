"""Homeopathy case-taking fields (draft, pending review by practising homeopaths): 108 fields.

The first 38 were generated from docs/planning/health-history-field-review-2026-10.md (rows H1-H38). The other 70 come from
the clinic's paper case form (two pages, Bengali), see PAPER_FORM_FIELDS; edit by hand from here.
Keep the labels in frontend/src/messages/{en,bn}/caseTaking.json in step: tests/integration/test_case_taking.py
fails if a key, group or option has no label.
"""

from app.shared.case_taking import Field, System

YES_NO = ("yes", "no")


def _text(key: str, group: str, scope: str = "patient", length: int = 100, **kw) -> Field:
    """A short written answer, for the lines of the paper form that have no choices to tick."""
    return Field(key=key, group=group, scope=scope, type="text", max_length=length, **kw)


def _one(key: str, group: str, options: tuple[str, ...], scope: str = "patient", **kw) -> Field:
    return Field(key=key, group=group, scope=scope, type="one", options=options, **kw)


# Fields taken from the paper case form (two pages, Bengali). Where the form gives boxes to tick the answer is a choice;
# where it only gives a line to write on it is short text, so the clinic's homeopaths can later set the real choice
# lists. Sensitive ones (suicidal tendency, sexual and reproductive history) are shown only to people who hold
# `case_taking.sensitive`.
PAPER_FORM_FIELDS = (
    # --- body: functions and physical findings ---
    _one("build", "body", ("lean", "medium", "stout")),
    _one("sexual_desire", "body", ("increased", "normal", "diminished", "absent"), sensitive=True),
    _text("burning", "body", length=200),
    _text("skin_marks", "body", length=200),
    _text("skin_marks_type", "body", length=200),
    _text("urine_colour", "body", length=60),
    _text("urine_quantity", "body", length=60),
    _text("stool_colour", "body", length=60),
    _text("stool_type", "body", length=60),
    Field(key="offensive_odour", group="body", scope="patient", type="many", options=("sweat", "stool", "urine", "mouth")),
    _text("acidity", "body"),
    _one("catches_cold_easily", "body", YES_NO),
    _text("worm_symptoms", "body", length=200),
    _text("intolerances", "body", length=300),
    _text("appetite", "body"),
    _text("tongue", "body"),
    _text("tongue_colour", "body", length=60),
    _text("saliva", "body"),
    _text("saliva_type", "body"),
    _text("bathing", "body", length=200),
    _text("sleep", "body", length=200),
    _one("head_sweat_in_sleep", "body", YES_NO),
    # --- mind ---
    _text("temperament", "mind", length=200),
    _text("worries", "mind", length=200),
    _text("dream_setting", "mind"),
    _text("anger", "mind", length=200),
    _text("compassion", "mind"),
    _text("weeping", "mind"),
    _text("memory", "mind"),
    _text("own_decision", "mind", length=200),
    Field(key="company_manner", group="mind", scope="patient", type="many", options=("timid", "brave")),
    _one("suicidal_tendency", "mind", YES_NO, sensitive=True),
    _text("patience", "mind"),
    _text("talkativeness", "mind"),
    _text("noise_sensitivity", "mind"),
    _text("hurry", "mind"),
    _text("self_importance", "mind"),
    _text("easily_startled", "mind"),
    _text("cleanliness", "mind"),
    _text("religious_fanaticism", "mind"),
    _text("shyness", "mind"),
    _text("obstinacy", "mind"),
    _text("someone_behind", "mind"),
    _text("travel", "mind"),
    _one("public_speaking", "mind", ("shyness", "fear", "normal")),
    _text("indecision", "mind"),
    _one("cleverness", "mind", ("simple", "foolish", "clever")),
    _one("labour", "mind", ("likes", "dislikes", "lazy")),
    _one("criticism", "mind", ("likes", "dislikes")),
    # --- women ---
    _text("menses_colour", "women", length=60),
    _text("menstrual_flow_type", "women"),
    _text("menstrual_symptoms", "women", length=300),
    _text("leucorrhoea_colour", "women", length=60),
    _text("leucorrhoea_type", "women"),
    _text("discharge_odour", "women"),
    Field(key="pregnancy_months", group="women", scope="patient", type="quantity", units=("months",)),
    Field(key="abortion_count", group="women", scope="patient", type="quantity", units=("times",), sensitive=True),
    _text("abortion_month", "women", length=60, sensitive=True),
    _text("vaginal_passage", "women", length=300, sensitive=True),
    # --- children ---
    _text("teething", "children"),
    _one("walking_talking", "children", ("on_time", "late")),
    _text("feeding", "children", length=200),
    _text("bedwetting", "children"),
    # --- history ---
    _text("past_illnesses", "history", length=500),
    _text("vaccination_animal_bite", "history", length=300),
    _text("lab_report", "history", length=500),
    # --- the visit: chief complaints and the prescription tracker ---
    Field(key="chief_complaints", group="complaint", scope="visit", type="table", max_rows=12, columns=(_text("complaint", "complaint", "visit", 200),)),
    Field(
        key="prescribed", group="prescription", scope="visit", type="table", max_rows=10,
        columns=(
            _one("kind", "prescription", ("dilution", "mother_tincture", "biochemic", "other"), "visit"),
            _text("name", "prescription", "visit", 100),
            _text("potency", "prescription", "visit", 30),
        ),
    ),
    _text("new_symptoms", "prescription", "visit", 300),
    Field(key="next_remedies", group="prescription", scope="visit", type="table", max_rows=3, columns=(_text("remedy", "prescription", "visit", 100),)),
)

EXISTING_FIELDS = (
    Field(key="location", group="complaint", scope="visit", type="text"),
    Field(key="sensation", group="complaint", scope="visit", type="many", options=('burning', 'stitching', 'throbbing', 'cutting', 'pressing', 'cramping', 'tearing', 'bursting', 'dull', 'sharp', 'itching', 'numbness')),
    Field(key="onset", group="complaint", scope="visit", type="one", options=('sudden', 'gradual')),
    Field(key="duration", group="complaint", scope="visit", type="quantity", units=('days', 'weeks', 'months', 'years')),
    Field(key="causation", group="complaint", scope="visit", type="many", options=('grief', 'fright', 'anger', 'shock', 'suppressed_emotion', 'injury', 'vaccination', 'suppressed_discharge', 'cold_wet', 'overwork', 'after_illness')),
    Field(key="worse_from", group="complaint", scope="visit", type="many", options=('morning', 'afternoon', 'evening', 'night', 'heat', 'cold', 'damp', 'weather_change', 'motion', 'rest', 'lying_left', 'lying_right', 'touch', 'pressure', 'eating', 'drinking', 'sleep', 'company', 'solitude')),
    Field(key="better_from", group="complaint", scope="visit", type="many", options=('morning', 'afternoon', 'evening', 'night', 'heat', 'cold', 'damp', 'weather_change', 'motion', 'rest', 'lying_left', 'lying_right', 'touch', 'pressure', 'eating', 'drinking', 'sleep', 'company', 'solitude')),
    Field(key="accompanying", group="complaint", scope="visit", type="text", max_length=1000),
    Field(key="side_affected", group="complaint", scope="visit", type="one", options=('right', 'left', 'both', 'alternating')),
    Field(key="thermal_state", group="generals", scope="patient", type="one", options=('chilly', 'hot', 'ambithermal')),
    Field(key="thirst", group="generals", scope="patient", type="one", options=('thirstless', 'little', 'moderate', 'large')),
    Field(key="water_preference", group="generals", scope="patient", type="one", options=('cold', 'warm', 'none')),
    Field(key="food_desires", group="generals", scope="patient", type="many", options=('sweet', 'salty', 'sour', 'spicy', 'fatty', 'milk', 'eggs', 'meat', 'fish', 'cold_drinks', 'hot_drinks')),
    Field(key="food_aversions", group="generals", scope="patient", type="many", options=('sweet', 'salty', 'sour', 'spicy', 'fatty', 'milk', 'eggs', 'meat', 'fish', 'cold_drinks', 'hot_drinks')),
    Field(key="perspiration", group="generals", scope="patient", type="one", options=('none', 'scanty', 'moderate', 'profuse')),
    Field(key="perspiration_odour", group="generals", scope="patient", type="one", options=('none', 'offensive')),
    Field(key="perspiration_where", group="generals", scope="patient", type="text"),
    Field(key="sleep_position", group="generals", scope="patient", type="one", options=('back', 'left', 'right', 'abdomen', 'any')),
    Field(key="dreams", group="generals", scope="patient", type="text"),
    Field(key="menstrual_cycle", group="generals", scope="patient", type="one", options=('regular', 'irregular')),
    Field(key="menstrual_flow", group="generals", scope="patient", type="one", options=('scanty', 'normal', 'heavy')),
    Field(key="menstrual_pain", group="generals", scope="patient", type="one", options=('none', 'before', 'during', 'after')),
    Field(key="leucorrhoea", group="generals", scope="patient", type="one", options=('none', 'mild', 'profuse')),
    Field(key="fears", group="mind", scope="patient", type="many", options=('dark', 'alone', 'death', 'disease', 'animals', 'heights', 'crowd', 'exams')),
    Field(key="mood_tendencies", group="mind", scope="patient", type="many", options=('anxious', 'irritable', 'weepy', 'sad', 'restless', 'suspicious', 'jealous', 'indifferent', 'cheerful')),
    Field(key="consolation", group="mind", scope="patient", type="one", options=('better', 'worse', 'none')),
    Field(key="company", group="mind", scope="patient", type="one", options=('desire', 'aversion', 'none')),
    Field(key="childhood_illnesses", group="history", scope="patient", type="many", options=('measles', 'chickenpox', 'mumps', 'whooping_cough', 'typhoid', 'jaundice', 'tonsillitis', 'worms')),
    Field(key="suppressive_history", group="history", scope="patient", type="many", options=('steroid_cream', 'antibiotics', 'antihistamines', 'painkillers', 'vaccine_reaction')),
    Field(key="previous_remedies", group="history", scope="patient", type="table", columns=(Field(key="remedy", group="history", scope="patient", type="text", max_length=100), Field(key="potency", group="history", scope="patient", type="text", max_length=30), Field(key="response", group="history", scope="patient", type="one", options=("better", "same", "worse")))),
    Field(key="miasms", group="history", scope="patient", type="many", options=('psora', 'sycosis', 'syphilis', 'tubercular')),
    Field(key="remedy", group="prescription", scope="visit", type="text"),
    Field(key="potency", group="prescription", scope="visit", type="one", options=('6c', '30c', '200c', '1m', '10m', 'lm', 'mt')),
    Field(key="dose_form", group="prescription", scope="visit", type="one", options=('pills', 'liquid', 'powder', 'tablet')),
    Field(key="repetition", group="prescription", scope="visit", type="one", options=('single', 'daily', 'twice_daily', 'weekly', 'as_needed')),
    Field(key="avoid", group="prescription", scope="visit", type="many", options=('coffee', 'camphor', 'mint', 'strong_smells')),
    Field(key="response", group="prescription", scope="visit", type="one", options=('better', 'same', 'worse', 'aggravation_then_better', 'new_symptom')),
    Field(key="next_step", group="prescription", scope="visit", type="one", options=('continue', 'change_potency', 'change_remedy', 'wait')),
)

FIELDS = EXISTING_FIELDS + PAPER_FORM_FIELDS


def _contradictions(scope: str, data: dict) -> dict[str, str]:
    """Answers that cannot both be true. Each message names the clash so the doctor can fix the right field."""
    if scope != "patient":
        return {}
    errors: dict[str, str] = {}
    clash = sorted(set(data.get("food_desires", [])) & set(data.get("food_aversions", [])))
    if clash:
        errors["food_aversions"] = f"cannot also be a craving: {', '.join(clash)}"
    if data.get("perspiration") == "none":
        if data.get("perspiration_odour") == "offensive":
            errors["perspiration_odour"] = "cannot be offensive when there is no perspiration"
        if "sweat" in data.get("offensive_odour", []):
            errors["offensive_odour"] = "cannot include sweat when there is no perspiration"
    return errors


HOMEOPATHY = System(
    key="homeopathy",
    fields=FIELDS,
    groups=(
        ("complaint", "visit"),
        ("generals", "patient"),
        ("body", "patient"),
        ("mind", "patient"),
        ("women", "patient"),
        ("children", "patient"),
        ("history", "patient"),
        ("prescription", "visit"),
    ),
    rules=(_contradictions,),
)
