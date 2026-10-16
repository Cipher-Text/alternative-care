"""Build the catalogue seed files from raw/*.json and the curation decisions.

    python -m scripts.catalogue.build            # from backend/, writes seed_data/ and prints a report
    python -m scripts.catalogue.build --check    # fails if seed_data/ is not what the build would write
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from scripts.catalogue import curation as cur

BACKEND = Path(__file__).resolve().parents[2]
RAW = BACKEND.parent / "raw"
SEED = BACKEND / "seed_data"


def _load(path: Path, key: str) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))[key]


def _dump(path: Path, payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def revise_medicines(raw: list[dict]) -> tuple[list[dict], list[dict]]:
    medicines, aliases = [], []
    for m in raw:
        out = {k: v for k, v in m.items() if k not in ("aliases_en", "aliases_bn")}
        if str(out.get("potency") or "").strip().lower() in cur.EMPTY_POTENCY:
            out["potency"] = None
        if str(out.get("dosage_guidance_en") or "").startswith(cur.DISCLAIMER_DOSAGE_PREFIX):
            out["dosage_guidance_en"] = None
            out["dosage_guidance_bn"] = None
        medicines.append(out)

        seen: set[tuple[str | None, str | None]] = set()

        def add(en: str | None, bn: str | None, kind: str, priority: int) -> None:
            en = en.strip() if en else None
            bn = bn.strip() if bn else None
            if en and en.lower() == m["name_en"].lower():
                en = None
            if bn and bn == m.get("name_bn"):
                bn = None
            if not en and not bn:
                return
            key = ((en or "").lower() or None, bn)
            if key in seen:
                return
            seen.add(key)
            aliases.append({"medicine_name_en": m["name_en"], "system": m["system"], "alias_en": en, "alias_bn": bn,
                            "alias_type": kind, "priority": priority})

        for en, bn in zip(m.get("aliases_en") or [], m.get("aliases_bn") or []):
            add(en, bn, cur.C, 6)
        for extra in (m.get("aliases_en") or [])[len(m.get("aliases_bn") or []):]:
            add(extra, None, cur.C, 6)
        for en, bn, kind in cur.MEDICINE_ALIASES.get(m["name_en"], []):
            add(en, bn, kind, 5)
    return medicines, aliases


def revise_symptoms(raw: list[dict]) -> tuple[list[dict], list[dict]]:
    symptoms, aliases = list(raw), []
    for s in raw:
        seen: set[tuple[str | None, str | None]] = set()
        for en, bn, kind in cur.SYMPTOM_ALIASES.get(s["name_en"], []):
            if en and en.lower() == s["name_en"].lower():
                en = None
            if bn and bn == s.get("name_bn"):
                bn = None
            if not en and not bn:
                continue
            key = ((en or "").lower() or None, bn)
            if key in seen:
                continue
            seen.add(key)
            aliases.append({"symptom_name_en": s["name_en"], "alias_en": en, "alias_bn": bn, "alias_type": kind, "priority": 5})
    return symptoms, aliases


def _find(text: str, term: str) -> list[int]:
    """Whole-word hits. A term written "^cold" only counts as a listed item of its own ("Cold, cough, fever"), because a bare
    "cold" mostly means temperature ("worse in cold air", "cold to touch")."""
    if term.startswith("^"):
        return [m.start(1) for m in re.finditer(rf"(?:^|[,;.]\s*)({re.escape(term[1:])})\s*(?=[,;.]|$)", text)]
    return [m.start() for m in re.finditer(rf"(?<![\w-]){re.escape(term)}(?![\w-])", text)]


def _negated(text: str, pos: int) -> bool:
    clause = re.split(r"[,;.]", text[max(0, pos - 40):pos])[-1]  # a negation only reaches to the end of its own clause
    before = re.findall(r"[a-z']+", clause)[-4:]
    return any(w in cur.NEGATIONS for w in before)


def derive_mappings(medicines: list[dict], valid_symptoms: set[str]) -> list[dict]:
    links = []
    for m in medicines:
        text = (m.get("indications_en") or "").lower()
        if not text:
            continue
        for symptom, terms in cur.SYMPTOM_TERMS.items():
            if symptom not in valid_symptoms:
                continue
            hits: dict[str, int] = {}
            for term in terms:
                for pos in _find(text, term):
                    if not _negated(text, pos):
                        hits[term] = min(hits.get(term, pos), pos)
            if not hits:
                continue
            specific = [t for t in hits if t not in cur.GENERIC_TERMS]
            strength = 2 if not specific else 3
            if specific and min(hits[t] for t in specific) < 60:
                strength += 1  # named among the first things the text lists
            if len(specific) >= 2:
                strength += 1
            links.append({"medicine_name_en": m["name_en"], "system": m["system"], "symptom_name_en": symptom,
                          "strength": min(strength, 5), "matched_terms": sorted(hits)})
    links.sort(key=lambda l: (l["medicine_name_en"], l["symptom_name_en"]))
    return links


def build() -> tuple[dict[str, str], str]:
    raw_meds = _load(RAW / "medicines.json", "medicines")
    raw_syms = _load(RAW / "symptoms.json", "symptoms")
    raw_links = json.loads((RAW / "medicine_symptoms.json").read_text(encoding="utf-8"))["links"]

    medicines, med_aliases = revise_medicines(raw_meds)
    symptoms, sym_aliases = revise_symptoms(raw_syms)
    names = {s["name_en"] for s in symptoms}
    unknown = sorted(set(cur.SYMPTOM_TERMS) - names)
    if unknown:
        raise SystemExit(f"curation names symptoms that do not exist: {unknown}")
    missing_med = sorted(set(cur.MEDICINE_ALIASES) - {m["name_en"] for m in medicines})
    missing_sym = sorted(set(cur.SYMPTOM_ALIASES) - names)
    if missing_med or missing_sym:
        raise SystemExit(f"curation names rows that do not exist: medicines {missing_med}, symptoms {missing_sym}")
    links = derive_mappings(medicines, names)

    old = {(l["medicine_name_en"], l["symptom_name_en"]) for l in raw_links}
    new = {(l["medicine_name_en"], l["symptom_name_en"]) for l in links}
    linked = {l["symptom_name_en"] for l in links}
    report = [
        f"medicines {len(medicines)}, aliases {len(med_aliases)}",
        f"symptoms {len(symptoms)}, aliases {len(sym_aliases)}",
        f"links raw {len(old)} -> revised {len(new)}  (kept {len(old & new)}, dropped {len(old - new)}, added {len(new - old)})",
        f"strength spread {dict(sorted(Counter(l['strength'] for l in links).items()))}",
        f"symptoms with no medicine: {sorted(names - linked)}",
    ]
    for label, pairs in (("dropped", old - new), ("added", new - old)):
        for med, sym in sorted(pairs):
            report.append(f"  {label}: {med} -> {sym}")

    files = {
        "medicines.json": _dump(SEED / "medicines.json", {"medicines": medicines}),
        "symptoms.json": _dump(SEED / "symptoms.json", {"symptoms": symptoms}),
        "medicine_aliases.json": _dump(SEED / "medicine_aliases.json", {"aliases": med_aliases}),
        "symptom_aliases.json": _dump(SEED / "symptom_aliases.json", {"aliases": sym_aliases}),
        "medicine_symptom_mappings.json": _dump(SEED / "medicine_symptom_mappings.json", {"mappings": links}),
    }
    return files, "\n".join(report)


def main() -> int:
    files, report = build()
    if "--check" in sys.argv:
        stale = [n for n, body in files.items() if not (SEED / n).exists() or (SEED / n).read_text(encoding="utf-8") != body]
        print("seed_data is current" if not stale else f"stale: {stale}")
        return 1 if stale else 0
    for name, body in files.items():
        (SEED / name).write_text(body, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
