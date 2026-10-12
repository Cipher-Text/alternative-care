"""Homeopathy case-taking fields (draft v1, pending review by practising homeopaths).

Generated once from docs/planning/health-history-field-review-2026-10.md (rows H1-H38); edit by hand from here.
Keep the labels in frontend/src/messages/{en,bn}/caseTaking.json in step: tests/integration/test_case_taking.py
fails if a key, group or option has no label.
"""

from app.shared.case_taking import Field, System

FIELDS = (
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
    Field(key="dominant_miasm", group="history", scope="patient", type="one", options=('psora', 'sycosis', 'syphilis', 'tubercular')),
    Field(key="remedy", group="prescription", scope="visit", type="text"),
    Field(key="potency", group="prescription", scope="visit", type="one", options=('6c', '30c', '200c', '1m', '10m', 'lm', 'mt')),
    Field(key="dose_form", group="prescription", scope="visit", type="one", options=('pills', 'liquid', 'powder', 'tablet')),
    Field(key="repetition", group="prescription", scope="visit", type="one", options=('single', 'daily', 'twice_daily', 'weekly', 'as_needed')),
    Field(key="avoid", group="prescription", scope="visit", type="many", options=('coffee', 'camphor', 'mint', 'strong_smells')),
    Field(key="response", group="prescription", scope="visit", type="one", options=('better', 'same', 'worse', 'aggravation_then_better', 'new_symptom')),
    Field(key="next_step", group="prescription", scope="visit", type="one", options=('continue', 'change_potency', 'change_remedy', 'wait')),
)

HOMEOPATHY = System(
    key="homeopathy",
    fields=FIELDS,
    groups=(
        ("complaint", "visit"),
        ("generals", "patient"),
        ("mind", "patient"),
        ("history", "patient"),
        ("prescription", "visit"),
    ),
)
