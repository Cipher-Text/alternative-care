"""Fixed option lists for patient health history (stored as these codes; labels live in the frontend's
translation files, English and Bengali).

Safety-related lists (allergies, red flags, chronic conditions, pregnancy) are closed on purpose: a free-text
typo must never hide a warning. The doctor's own words go in the free-text notes next to them.
"""

CHRONIC_CONDITIONS = (
    "diabetes", "hypertension", "asthma_copd", "heart_disease", "kidney_disease", "liver_disease",
    "thyroid_disorder", "tuberculosis", "epilepsy", "cancer", "skin_disease", "arthritis",
    "mental_health", "anaemia",
)
ALLERGY_TYPES = ("drug", "food", "herb", "dust_pollen", "skin_contact", "insect", "other")
ALLERGY_SEVERITIES = ("mild", "moderate", "severe")
FAMILY_HISTORY = (
    "diabetes", "hypertension", "heart_disease", "tuberculosis", "cancer", "asthma", "mental_illness",
    "epilepsy", "thyroid_disorder",
)
HABIT_STATUSES = ("never", "former", "current")
DIET_TYPES = ("vegetarian", "non_vegetarian", "mixed")
RED_FLAGS = (
    "chest_pain", "breathlessness", "severe_bleeding", "infant_high_fever", "loss_of_consciousness",
    "sudden_severe_headache", "sudden_weakness", "persistent_vomiting",
)
REFERRAL_URGENCIES = ("none", "routine", "urgent", "emergency")
BLOOD_SUGAR_TYPES = ("fasting", "random", "postprandial")

# Warnings shown on the patient and prescription screens, derived from the profile and the patient's age
SAFETY_FLAGS = (
    "allergy", "pregnant", "breastfeeding", "child_under_5", "elderly_65_plus", "on_allopathic_medicines",
    "on_blood_thinners", "recent_surgery",
)

OPTIONS: dict[str, tuple[str, ...]] = {
    "chronic_conditions": CHRONIC_CONDITIONS,
    "allergy_types": ALLERGY_TYPES,
    "allergy_severities": ALLERGY_SEVERITIES,
    "family_history": FAMILY_HISTORY,
    "habit_statuses": HABIT_STATUSES,
    "diet_types": DIET_TYPES,
    "red_flags": RED_FLAGS,
    "referral_urgencies": REFERRAL_URGENCIES,
    "blood_sugar_types": BLOOD_SUGAR_TYPES,
    "safety_flags": SAFETY_FLAGS,
}
