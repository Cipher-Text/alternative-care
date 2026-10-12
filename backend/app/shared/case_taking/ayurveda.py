"""Ayurveda case-taking fields (draft v1, pending review by practising Ayurveda doctors).

Generated once from docs/planning/health-history-field-review-2026-10.md (rows A1-A32); edit by hand from here.
Keep the labels in frontend/src/messages/{en,bn}/caseTaking.json in step: tests/integration/test_case_taking.py
fails if a key, group or option has no label.

Taken once and kept up to date (patient): prakriti, koshtha, build, strength and capacities, tastes, earlier
rasa-shastra use. Taken at each visit: the present imbalance, the eight-fold examination, the causes and the treatment.
"""

from app.shared.case_taking import Field, System

FIELDS = (
    Field(key="prakriti", group="constitution", scope="patient", type="one", options=('vata', 'pitta', 'kapha', 'vata_pitta', 'pitta_kapha', 'vata_kapha', 'tridosha')),
    Field(key="koshtha", group="constitution", scope="patient", type="one", options=('mridu', 'madhyama', 'krura')),
    Field(key="akriti", group="constitution", scope="patient", type="one", options=('thin', 'medium', 'heavy')),
    Field(key="bala", group="capacity", scope="patient", type="one", options=('good', 'medium', 'poor')),
    Field(key="satva", group="capacity", scope="patient", type="one", options=('strong', 'medium', 'weak')),
    Field(key="ahara_shakti", group="capacity", scope="patient", type="one", options=('good', 'medium', 'poor')),
    Field(key="vyayama_shakti", group="capacity", scope="patient", type="one", options=('good', 'medium', 'poor')),
    Field(key="vaya", group="capacity", scope="patient", type="one", options=('bala', 'madhya', 'vriddha')),
    Field(key="preferred_tastes", group="capacity", scope="patient", type="many", options=('madhura', 'amla', 'lavana', 'katu', 'tikta', 'kashaya')),
    Field(key="rasashastra_history", group="history", scope="patient", type="one", options=('yes', 'no', 'unknown')),
    Field(key="vikriti", group="current", scope="visit", type="one", options=('vata', 'pitta', 'kapha', 'vata_pitta', 'pitta_kapha', 'vata_kapha', 'tridosha')),
    Field(key="agni", group="current", scope="visit", type="one", options=('sama', 'vishama', 'tikshna', 'manda')),
    Field(key="ama", group="current", scope="visit", type="one", options=('absent', 'mild', 'moderate', 'marked')),
    Field(key="nadi", group="examination", scope="visit", type="one", options=('vata', 'pitta', 'kapha', 'mixed')),
    Field(key="mutra", group="examination", scope="visit", type="many", options=('normal', 'increased', 'reduced', 'burning', 'turbid', 'frequent_night')),
    Field(key="mala", group="examination", scope="visit", type="one", options=('normal', 'hard', 'loose', 'sticky', 'undigested')),
    Field(key="jihva", group="examination", scope="visit", type="one", options=('clean', 'white', 'yellow', 'thick', 'cracked', 'red')),
    Field(key="shabda", group="examination", scope="visit", type="one", options=('normal', 'hoarse', 'weak', 'loud')),
    Field(key="sparsha", group="examination", scope="visit", type="many", options=('warm', 'cool', 'dry', 'oily', 'rough', 'moist')),
    Field(key="drik", group="examination", scope="visit", type="many", options=('normal', 'dull', 'red', 'yellowish', 'dry', 'watery')),
    Field(key="nidana", group="cause", scope="visit", type="many", options=('improper_diet', 'irregular_meals', 'day_sleep', 'night_waking', 'suppressed_urges', 'stress', 'too_much_exercise', 'too_little_exercise', 'seasonal')),
    Field(key="doshas_involved", group="cause", scope="visit", type="many", options=('vata', 'pitta', 'kapha')),
    Field(key="dhatus_involved", group="cause", scope="visit", type="many", options=('rasa', 'rakta', 'mamsa', 'meda', 'asthi', 'majja', 'shukra')),
    Field(key="srotas_involved", group="cause", scope="visit", type="many", options=('pranavaha', 'annavaha', 'udakavaha', 'rasavaha', 'raktavaha', 'mamsavaha', 'medovaha', 'asthivaha', 'majjavaha', 'shukravaha', 'mutravaha', 'purishavaha', 'svedavaha', 'artavavaha', 'manovaha')),
    Field(key="desha", group="cause", scope="visit", type="one", options=('anupa', 'jangala', 'sadharana')),
    Field(key="ritu", group="cause", scope="visit", type="one", options=('vasanta', 'grishma', 'varsha', 'sharad', 'hemanta', 'shishira')),
    Field(key="treatment_approach", group="treatment", scope="visit", type="one", options=('shamana', 'shodhana', 'both')),
    Field(key="panchakarma", group="treatment", scope="visit", type="many", options=('vamana', 'virechana', 'basti', 'nasya', 'raktamokshana')),
    Field(key="formulation", group="treatment", scope="visit", type="text"),
    Field(key="anupana", group="treatment", scope="visit", type="one", options=('warm_water', 'honey', 'ghee', 'milk', 'buttermilk', 'other')),
    Field(key="when_to_take", group="treatment", scope="visit", type="one", options=('before_food', 'after_food', 'empty_stomach', 'bedtime')),
    Field(key="diet_lifestyle_advice", group="treatment", scope="visit", type="text", max_length=1000),
)

AYURVEDA = System(
    key="ayurveda",
    fields=FIELDS,
    groups=(
        ("constitution", "patient"),
        ("capacity", "patient"),
        ("history", "patient"),
        ("current", "visit"),
        ("examination", "visit"),
        ("cause", "visit"),
        ("treatment", "visit"),
    ),
)
