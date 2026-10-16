"""SeedData completes catalogue rows, adds aliases and mappings, and never overwrites or duplicates on a second run."""
import pytest
from sqlalchemy import func, select

from app.shared.models import Medicine, MedicineAlias, MedicineSymptomMapping, Symptom, SymptomAlias
from scripts.seed import SeedData

pytestmark = pytest.mark.asyncio


async def _count(db, model) -> int:
    return (await db.execute(select(func.count()).select_from(model))).scalar_one()


async def test_seed_is_idempotent_and_keeps_admin_edits(db_session):
    seeder = SeedData(db_session)
    await seeder.seed_medicines("unused")
    await seeder.seed_symptoms("unused")
    first = await seeder.seed_catalogue_links()
    assert first["mappings"] > 500 and first["medicine_aliases"] > 100 and first["symptom_aliases"] > 50
    assert first["skipped"] == 0

    # an admin retunes one link, and a seed row carries an old placeholder
    link = (await db_session.execute(select(MedicineSymptomMapping).limit(1))).scalar_one()
    link.strength = 9
    medicine = (await db_session.execute(select(Medicine).where(Medicine.system == "homeopathy").limit(1))).scalar_one()
    medicine.potency = "Not specified"
    await db_session.flush()
    link_id, medicine_id = link.id, medicine.id

    await seeder.seed_medicines("unused")
    again = await seeder.seed_catalogue_links()
    assert again == {"medicine_aliases": 0, "symptom_aliases": 0, "mappings": 0, "skipped": 0}
    db_session.expire_all()
    assert (await db_session.get(MedicineSymptomMapping, link_id)).strength == 9
    assert (await db_session.get(Medicine, medicine_id)).potency is None
    assert await _count(db_session, MedicineAlias) == first["medicine_aliases"]
    assert await _count(db_session, SymptomAlias) == first["symptom_aliases"]
    assert await _count(db_session, Symptom) == 97
