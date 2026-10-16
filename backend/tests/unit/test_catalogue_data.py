"""The catalogue seed files are internally consistent and match what scripts/catalogue/build.py would write."""
import json
from pathlib import Path

from scripts.catalogue import build as catalogue_build
from scripts.catalogue.build import SEED

def _load(name: str, key: str) -> list[dict]:
    return json.loads((SEED / name).read_text(encoding="utf-8"))[key]


def test_seed_files_are_what_the_build_writes():
    files, _ = catalogue_build.build()
    for name, body in files.items():
        assert (SEED / name).read_text(encoding="utf-8") == body, f"{name} is stale: run python -m scripts.catalogue.build"


def test_medicines_have_no_placeholder_text():
    for m in _load("medicines.json", "medicines"):
        assert m.get("potency") != "Not specified", m["name_en"]
        assert not (m.get("dosage_guidance_en") or "").startswith("No evidence-based dose"), m["name_en"]
        assert m["is_global"] is True


def test_names_are_unique_per_system():
    medicines = _load("medicines.json", "medicines")
    assert len({(m["name_en"], m["system"]) for m in medicines}) == len(medicines)
    symptoms = _load("symptoms.json", "symptoms")
    assert len({s["name_en"] for s in symptoms}) == len(symptoms)


def test_aliases_point_at_real_rows_and_never_repeat_the_name():
    medicines = {(m["name_en"], m["system"]): m for m in _load("medicines.json", "medicines")}
    for a in _load("medicine_aliases.json", "aliases"):
        m = medicines[(a["medicine_name_en"], a["system"])]
        assert a["alias_en"] or a["alias_bn"]
        assert (a["alias_en"] or "").lower() != m["name_en"].lower()
        assert a["alias_bn"] != m["name_bn"]
    symptoms = {s["name_en"]: s for s in _load("symptoms.json", "symptoms")}
    for a in _load("symptom_aliases.json", "aliases"):
        s = symptoms[a["symptom_name_en"]]
        assert a["alias_en"] or a["alias_bn"]
        assert (a["alias_en"] or "").lower() != s["name_en"].lower()


def test_mappings_are_valid_unique_and_in_range():
    medicines = {(m["name_en"], m["system"]) for m in _load("medicines.json", "medicines")}
    symptoms = {s["name_en"] for s in _load("symptoms.json", "symptoms")}
    links = _load("medicine_symptom_mappings.json", "mappings")
    pairs = [(l["medicine_name_en"], l["symptom_name_en"]) for l in links]
    assert len(pairs) == len(set(pairs))
    for l in links:
        assert (l["medicine_name_en"], l["system"]) in medicines
        assert l["symptom_name_en"] in symptoms
        assert 1 <= l["strength"] <= 5
        assert l["matched_terms"]


def test_negated_and_look_alike_phrases_do_not_make_links():
    # "croup-like", "no thirst during fever" and "diabetic carbuncle" are not indications for Croup / Fever / Diabetes
    pairs = {(l["medicine_name_en"], l["symptom_name_en"]) for l in _load("medicine_symptom_mappings.json", "mappings")}
    assert ("Aconitum Napellus", "Croup") not in pairs
    assert ("Antimonium Crudum", "Fever") not in pairs
    assert ("Kaishora Guggulu", "Diabetes Symptoms") not in pairs
    assert ("Tulsi", "Cold") in pairs
    assert ("Nux Moschata", "Abdominal Bloating") in pairs  # "without thirst, bloating": the negation ends at the comma
