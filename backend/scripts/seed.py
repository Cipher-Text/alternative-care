#!/usr/bin/env python3
"""
Seed script for AltCare database.

Populates the database with:
- Bangladesh geographic data (divisions, districts, upazilas)
- Translation keys (English/Bengali)
- Sample tenants and users (for testing)

Usage:
    python scripts/seed.py

Features:
- Idempotent: Can be run multiple times safely
- Transactional: Rolls back on error
- Clear output: Shows what was created/skipped
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from scripts.demo_directory import seed_demo_directory
from scripts.demo_patients import seed_demo_patients
from scripts.demo_platform import seed_demo_platform
from app.shared.models import (
    Article,
    Institution,
    District,
    Division,
    Medicine,
    MedicineAlias,
    MedicineSymptomMapping,
    Pharmacy,
    Symptom,
    SymptomAlias,
    Tenant,
    Translation,
    Upazila,
    User,
)


class SeedData:
    """Seed data manager."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.seed_data_dir = Path(__file__).parent.parent / "seed_data"

    def load_json(self, filename: str) -> dict:
        """Load JSON file from seed_data directory."""
        file_path = self.seed_data_dir / filename
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def get_default_tenant_id(self) -> str:
        """Return a tenant ID for seeding tenant-scoped global catalog rows."""
        data = self.load_json("sample_data.json")
        tenants = data.get("tenants", [])
        if not tenants:
            raise RuntimeError("sample_data.json has no tenants for catalog seeding")
        return tenants[0]["id"]

    async def seed_geographic_data(self) -> dict[str, int]:
        """Seed divisions, districts, and upazilas."""
        data = self.load_json("geographic_data.json")
        stats = {"divisions": 0, "districts": 0, "upazilas": 0}

        # Seed divisions
        print("\n📍 Seeding geographic data...")
        for div_data in data["divisions"]:
            existing = await self.session.execute(
                select(Division).where(Division.id == div_data["id"])
            )
            if not existing.scalar_one_or_none():
                division = Division(**div_data)
                self.session.add(division)
                stats["divisions"] += 1

        # Seed districts
        for dist_data in data["districts"]:
            existing = await self.session.execute(
                select(District).where(District.id == dist_data["id"])
            )
            if not existing.scalar_one_or_none():
                district = District(**dist_data)
                self.session.add(district)
                stats["districts"] += 1

        # Seed upazilas
        for upazila_data in data["upazilas"]:
            existing = await self.session.execute(
                select(Upazila).where(Upazila.id == upazila_data["id"])
            )
            if not existing.scalar_one_or_none():
                upazila = Upazila(**upazila_data)
                self.session.add(upazila)
                stats["upazilas"] += 1

        await self.session.flush()
        return stats

    async def seed_translations(self) -> int:
        """Seed translation keys."""
        data = self.load_json("translations.json")
        count = 0

        print("\n🌐 Seeding translations...")
        for trans_data in data["translations"]:
            existing = await self.session.execute(
                select(Translation).where(Translation.key == trans_data["key"])
            )
            if not existing.scalar_one_or_none():
                translation = Translation(**trans_data)
                self.session.add(translation)
                count += 1

        await self.session.flush()
        return count

    async def seed_sample_data(self) -> dict[str, int]:
        """Seed sample tenants and users."""
        data = self.load_json("sample_data.json")
        stats = {"tenants": 0, "users": 0}

        print("\n👥 Seeding sample tenants and users...")

        # Seed tenants
        for tenant_data in data["tenants"]:
            existing = await self.session.execute(
                select(Tenant).where(Tenant.id == tenant_data["id"])
            )
            if not existing.scalar_one_or_none():
                tenant_dict = tenant_data.copy()
                # Set timestamps
                now = datetime.now(timezone.utc)
                tenant_dict["created_at"] = now
                tenant_dict["updated_at"] = now
                tenant_dict["plan_started_at"] = now

                if tenant_dict.get("is_verified"):
                    tenant_dict["verified_at"] = now
                if tenant_dict.get("is_approved"):
                    tenant_dict["approved_at"] = now

                tenant = Tenant(**tenant_dict)
                self.session.add(tenant)
                stats["tenants"] += 1

        await self.session.flush()

        # Seed users
        for user_data in data["users"]:
            existing = await self.session.execute(
                select(User).where(User.id == user_data["id"])
            )
            if not existing.scalar_one_or_none():
                user_dict = user_data.copy()

                # Hash password
                password = user_dict.pop("password")
                user_dict["password_hash"] = get_password_hash(password)

                # Set timestamps
                now = datetime.now(timezone.utc)
                user_dict["created_at"] = now
                user_dict["updated_at"] = now

                if user_dict.get("is_email_verified"):
                    user_dict["email_verified_at"] = now

                user = User(**user_dict)
                self.session.add(user)
                stats["users"] += 1

        await self.session.flush()
        return stats

    @staticmethod
    def _fill_gaps(row, data: dict) -> bool:
        """Complete an existing catalogue row from the seed file without overwriting what an admin edited: only empty columns
        are filled, and the two placeholders earlier seed files wrote (potency "Not specified", the "no evidence-based dose"
        text in the dosage field) are cleared."""
        changed = False
        for key, value in data.items():
            if key in ("is_global", "is_active") or value is None:
                continue
            if getattr(row, key, None) in (None, ""):
                setattr(row, key, value)
                changed = True
        if getattr(row, "potency", None) == "Not specified":
            row.potency = None
            changed = True
        if (getattr(row, "dosage_guidance_en", None) or "").startswith("No evidence-based dose"):
            row.dosage_guidance_en = row.dosage_guidance_bn = None
            changed = True
        return changed

    async def seed_medicines(self, tenant_id: str) -> int:
        """Seed medicines catalog; rows that exist are completed, not replaced."""
        data = self.load_json("medicines.json")
        count = 0
        self.medicines_completed = 0

        print("\n💊 Seeding medicines...")
        for medicine_data in data["medicines"]:
            existing = (await self.session.execute(
                select(Medicine).where(
                    Medicine.name_en == medicine_data["name_en"],
                    Medicine.system == medicine_data["system"]
                )
            )).scalar_one_or_none()
            if existing:
                self.medicines_completed += self._fill_gaps(existing, medicine_data)
            else:
                # is_global rows must have tenant_id=NULL (ck_medicines_tenant_global) —
                # only tenant-owned rows get the default tenant's id.
                row_tenant_id = None if medicine_data.get("is_global") else tenant_id
                medicine = Medicine(**medicine_data, tenant_id=row_tenant_id)
                self.session.add(medicine)
                count += 1

        await self.session.flush()
        return count

    async def seed_symptoms(self, tenant_id: str) -> int:
        """Seed symptoms catalog; rows that exist are completed, not replaced."""
        data = self.load_json("symptoms.json")
        count = 0
        self.symptoms_completed = 0

        print("\n🩺 Seeding symptoms...")
        for symptom_data in data["symptoms"]:
            existing = (await self.session.execute(
                select(Symptom).where(
                    Symptom.name_en == symptom_data["name_en"]
                )
            )).scalar_one_or_none()
            if existing:
                self.symptoms_completed += self._fill_gaps(existing, symptom_data)
            else:
                # is_global rows must have tenant_id=NULL (ck_symptoms_tenant_global) —
                # only tenant-owned rows get the default tenant's id.
                row_tenant_id = None if symptom_data.get("is_global") else tenant_id
                symptom = Symptom(**symptom_data, tenant_id=row_tenant_id)
                self.session.add(symptom)
                count += 1

        await self.session.flush()
        return count

    async def seed_articles(self) -> int:
        """Seed the starter blog posts and videos (backend/seed_data/articles.json), published and credited to the editorial team.

        They are written by the platform, not by a named clinician, so no reviewer is recorded: the public page shows a
        "reviewed by" line only when an admin signs an item off, and these have not been. An admin can open one, put it
        in review and publish it again with a reviewer's name once a practitioner has read it. Needs a platform admin
        user to own them; skipped (0) if there is none. Existing slugs are left alone.
        """
        admin = (await self.session.execute(select(User).where(User.role == "admin").order_by(User.created_at))).scalars().first()
        if admin is None:
            return 0
        have = set((await self.session.execute(select(Article.slug))).scalars())
        now = datetime.now(timezone.utc)
        count = 0
        print("\n📰 Seeding articles and videos...")
        for item in self.load_json("articles.json")["articles"]:
            if item["slug"] in have:
                continue
            self.session.add(Article(id=str(uuid.uuid4()), status="published", author_id=admin.id, author_name="AltCare সম্পাদকীয় দল",
                                     published_at=now, created_by=admin.id, updated_by=admin.id, **item))
            count += 1
        await self.session.flush()
        return count

    async def seed_catalogue_links(self) -> dict[str, int]:
        """Seed medicine/symptom aliases and the medicine<->symptom mappings, all global (tenant_id NULL).

        Needs the medicines and symptoms to exist already. Built by `python -m scripts.catalogue.build` from raw/. A link or
        alias that is already there is left exactly as it is, so a strength a platform admin changed is never reset.
        """
        medicines = {(m.name_en, m.system): m.id for m in (await self.session.execute(select(Medicine).where(Medicine.tenant_id.is_(None)))).scalars()}
        symptoms = {x.name_en: x.id for x in (await self.session.execute(select(Symptom).where(Symptom.tenant_id.is_(None)))).scalars()}
        stats = {"medicine_aliases": 0, "symptom_aliases": 0, "mappings": 0, "skipped": 0}

        print("\n🔗 Seeding aliases and medicine-symptom mappings...")
        have = {(a.medicine_id, (a.alias_en or "").lower(), a.alias_bn) for a in (await self.session.execute(select(MedicineAlias))).scalars()}
        for a in self.load_json("medicine_aliases.json")["aliases"]:
            medicine_id = medicines.get((a["medicine_name_en"], a["system"]))
            key = (medicine_id, (a["alias_en"] or "").lower(), a["alias_bn"])
            if medicine_id is None:
                stats["skipped"] += 1
            elif key not in have:
                have.add(key)
                self.session.add(MedicineAlias(medicine_id=medicine_id, tenant_id=None, alias_en=a["alias_en"], alias_bn=a["alias_bn"],
                                               alias_type=a["alias_type"], priority=a["priority"]))
                stats["medicine_aliases"] += 1

        have = {(a.symptom_id, (a.alias_en or "").lower(), a.alias_bn) for a in (await self.session.execute(select(SymptomAlias))).scalars()}
        for a in self.load_json("symptom_aliases.json")["aliases"]:
            symptom_id = symptoms.get(a["symptom_name_en"])
            key = (symptom_id, (a["alias_en"] or "").lower(), a["alias_bn"])
            if symptom_id is None:
                stats["skipped"] += 1
            elif key not in have:
                have.add(key)
                self.session.add(SymptomAlias(symptom_id=symptom_id, tenant_id=None, alias_en=a["alias_en"], alias_bn=a["alias_bn"],
                                              alias_type=a["alias_type"], priority=a["priority"]))
                stats["symptom_aliases"] += 1

        have = {(m.medicine_id, m.symptom_id) for m in (await self.session.execute(select(MedicineSymptomMapping))).scalars()}
        for link in self.load_json("medicine_symptom_mappings.json")["mappings"]:
            medicine_id = medicines.get((link["medicine_name_en"], link["system"]))
            symptom_id = symptoms.get(link["symptom_name_en"])
            if medicine_id is None or symptom_id is None:
                stats["skipped"] += 1
            elif (medicine_id, symptom_id) not in have:
                have.add((medicine_id, symptom_id))
                self.session.add(MedicineSymptomMapping(medicine_id=medicine_id, symptom_id=symptom_id, tenant_id=None, strength=link["strength"]))
                stats["mappings"] += 1

        await self.session.flush()
        return stats

    async def seed_pharmacies(self) -> int:
        """
        Seed the pharmacy directory from seed_data/pharmacies.json.

        Every row cites its `source_url`; the current file is the Hamdard (Unani) head office
        plus branch centres from the company's own website, read 2026-10-11. Nothing is
        `is_verified` and `last_confirmed_at` is left empty on purpose, so the practitioner UI says
        "not yet confirmed" until an admin has checked a listing. Districts are matched by English
        name against the seeded `districts` table; an unknown name fails loudly instead of
        silently dropping the location. Idempotent: a row whose name already exists in the same
        district is skipped.
        """
        data = self.load_json("pharmacies.json")
        districts = {
            name.lower(): district_id
            for district_id, name in (
                await self.session.execute(select(District.id, District.name_en))
            ).all()
        }
        existing = {
            (name.lower(), district_id)
            for name, district_id in (
                await self.session.execute(select(Pharmacy.name_en, Pharmacy.district_id))
            ).all()
        }

        count = 0
        print("\n💊 Seeding pharmacies...")
        for row in data["pharmacies"]:
            row = dict(row)
            district_name = row.pop("district", None)
            district_id = None
            if district_name:
                district_id = districts.get(district_name.lower())
                if district_id is None:
                    raise ValueError(
                        f"pharmacies.json: unknown district '{district_name}' for '{row['name_en']}'"
                    )
            if (row["name_en"].lower(), district_id) in existing:
                continue
            self.session.add(Pharmacy(**row, district_id=district_id))
            count += 1

        await self.session.flush()
        return count

    async def seed_institutions(self) -> int:
        """
        Seed the institution directory (Track D).

        Homeopathy (67 rows: 1 government + 66 private) comes from the
        Bangladesh Homeopathic Medical Education Council's own register
        (https://bhmec.gov.bd/home/colleges) — every row carries its
        `registration_code` and `source_url` for that reason. One code
        (029) is reused across two differently named institutions in that
        register itself; preserved as-is rather than silently altered.
        Unani/Ayurvedic (5 rows) has no comparable official online register
        found yet, so those are still web-search-sourced and explicitly
        partial — see docs/planning/future-scope-2026-09.md's addendum and
        the Institution model's docstring. None of the rows are
        `is_verified` — that flag means an admin has separately confirmed
        it, which seeding from a register doesn't do on its own.
        """
        data = self.load_json("institutions.json")
        count = 0

        print("\n🏫 Seeding institutions...")
        for institution_data in data["institutions"]:
            existing = await self.session.execute(
                select(Institution).where(Institution.name_en == institution_data["name_en"])
            )
            if not existing.scalar_one_or_none():
                institution = Institution(**institution_data)
                self.session.add(institution)
                count += 1

        await self.session.flush()
        return count


async def main():
    """Main seed function."""
    print("=" * 60)
    print("🌱 AltCare Database Seeding")
    print("=" * 60)

    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                seeder = SeedData(session)

                # Seed all data
                geo_stats = await seeder.seed_geographic_data()
                sample_stats = await seeder.seed_sample_data()
                default_tenant_id = await seeder.get_default_tenant_id()
                medicines_count = await seeder.seed_medicines(default_tenant_id)
                symptoms_count = await seeder.seed_symptoms(default_tenant_id)
                link_stats = await seeder.seed_catalogue_links()
                articles_count = await seeder.seed_articles()
                institutions_count = await seeder.seed_institutions()
                demo_stats = await seed_demo_patients(session) if settings.ENVIRONMENT == "development" else None
                if settings.ENVIRONMENT == "development":
                    await seed_demo_platform(session)
                    await seed_demo_directory(session)
                pharmacies_count = await seeder.seed_pharmacies()
                translations_count = await seeder.seed_translations()

                # Commit transaction
                await session.commit()

        # Print summary
        print("\n" + "=" * 60)
        print("✅ Seeding completed successfully!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"  • Divisions:     {geo_stats['divisions']:>3} created")
        print(f"  • Districts:     {geo_stats['districts']:>3} created")
        print(f"  • Upazilas:      {geo_stats['upazilas']:>3} created")
        print(f"  • Medicines:     {medicines_count:>3} created")
        print(f"  • Symptoms:      {symptoms_count:>3} created")
        print(f"  • Completed:     {seeder.medicines_completed} medicines, {seeder.symptoms_completed} symptoms already there")
        print(f"  • Aliases:       {link_stats['medicine_aliases']} medicine, {link_stats['symptom_aliases']} symptom created")
        print(f"  • Articles:      {articles_count:>3} created (blogs and videos)")
        print(f"  • Mappings:      {link_stats['mappings']:>3} created ({link_stats['skipped']} skipped)")
        print(f"  • Institutions:  {institutions_count:>3} created")
        print(f"  • Pharmacies:    {pharmacies_count:>3} created")
        print(f"  • Translations:  {translations_count:>3} created")
        print(f"  • Tenants:       {sample_stats['tenants']:>3} created")
        print(f"  • Users:         {sample_stats['users']:>3} created")
        if demo_stats:
            print(f"  • Demo patients: {demo_stats['patients']:>3} created, {demo_stats['accounts']} portal accounts, {demo_stats['links']} links")
        print("\n💡 Test credentials:")
        print("  • Doctor:     dr.rahman@example.com / Test@1234")
        print("  • Admin:      admin@altcare.com / Admin@1234")
        print("  • Operator:   operator@altcare.com / Operator@1234")
        print("  • Patient:    01700000001 or 01700000002, code 123456 (development only)")
        print("\n📚 Geographic data:")
        print("  • 8 divisions, 64 districts, 495 upazilas")
        print("\n💊 Medicines:")
        print("  • Homeopathy: Arnica, Belladonna, Nux Vomica, Pulsatilla, Rhus Tox")
        print("  • Ayurveda:   Ashwagandha, Triphala, Tulsi, Brahmi")
        print("  • Unani:      Kalonji, Senna")
        print("  • Herbal:     Turmeric, Ginger, Chamomile")
        print("\n🩺 Symptoms:")
        print("  • 25+ common symptoms across all categories")
        print("\n🏫 Institutions:")
        print("  • 67 homeopathic (official BHMEC register) + 5 unani/ayurvedic (web-search-sourced)")
        print("  • None marked is_verified yet — see Institution model docstring")
        print("\n🌐 Translations:")
        print("  • 80+ UI strings in English and Bengali")
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        print("\nNote: If you see 'duplicate key' errors, the data already exists.")
        print("This is normal - the script is idempotent and can be run multiple times.")
        raise


if __name__ == "__main__":
    asyncio.run(main())
