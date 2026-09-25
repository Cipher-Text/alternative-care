#!/usr/bin/env python3
"""
Seed script for AltCare database.

Populates the database with:
- Bangladesh geographic data (divisions, districts, upazilas)
- Integration providers catalog
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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.shared.models import (
    District,
    Division,
    IntegrationProvider,
    Medicine,
    Symptom,
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

    async def seed_integration_providers(self) -> int:
        """Seed integration providers catalog."""
        data = self.load_json("integration_providers.json")
        count = 0

        print("\n🔌 Seeding integration providers...")
        for provider_data in data["providers"]:
            existing = await self.session.execute(
                select(IntegrationProvider).where(
                    IntegrationProvider.name == provider_data["name"]
                )
            )
            if not existing.scalar_one_or_none():
                provider = IntegrationProvider(**provider_data)
                self.session.add(provider)
                count += 1

        await self.session.flush()
        return count

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

    async def seed_medicines(self, tenant_id: str) -> int:
        """Seed medicines catalog."""
        data = self.load_json("medicines.json")
        count = 0

        print("\n💊 Seeding medicines...")
        for medicine_data in data["medicines"]:
            existing = await self.session.execute(
                select(Medicine).where(
                    Medicine.name_en == medicine_data["name_en"],
                    Medicine.system == medicine_data["system"]
                )
            )
            if not existing.scalar_one_or_none():
                # is_global rows must have tenant_id=NULL (ck_medicines_tenant_global) —
                # only tenant-owned rows get the default tenant's id.
                row_tenant_id = None if medicine_data.get("is_global") else tenant_id
                medicine = Medicine(**medicine_data, tenant_id=row_tenant_id)
                self.session.add(medicine)
                count += 1

        await self.session.flush()
        return count

    async def seed_symptoms(self, tenant_id: str) -> int:
        """Seed symptoms catalog."""
        data = self.load_json("symptoms.json")
        count = 0

        print("\n🩺 Seeding symptoms...")
        for symptom_data in data["symptoms"]:
            existing = await self.session.execute(
                select(Symptom).where(
                    Symptom.name_en == symptom_data["name_en"]
                )
            )
            if not existing.scalar_one_or_none():
                # is_global rows must have tenant_id=NULL (ck_symptoms_tenant_global) —
                # only tenant-owned rows get the default tenant's id.
                row_tenant_id = None if symptom_data.get("is_global") else tenant_id
                symptom = Symptom(**symptom_data, tenant_id=row_tenant_id)
                self.session.add(symptom)
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
                providers_count = await seeder.seed_integration_providers()
                sample_stats = await seeder.seed_sample_data()
                default_tenant_id = await seeder.get_default_tenant_id()
                medicines_count = await seeder.seed_medicines(default_tenant_id)
                symptoms_count = await seeder.seed_symptoms(default_tenant_id)
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
        print(f"  • Providers:     {providers_count:>3} created")
        print(f"  • Medicines:     {medicines_count:>3} created")
        print(f"  • Symptoms:      {symptoms_count:>3} created")
        print(f"  • Translations:  {translations_count:>3} created")
        print(f"  • Tenants:       {sample_stats['tenants']:>3} created")
        print(f"  • Users:         {sample_stats['users']:>3} created")
        print("\n💡 Test credentials:")
        print("  • Doctor:     dr.rahman@example.com / Test@1234")
        print("  • Admin:      admin@altcare.com / Admin@1234")
        print("  • Operator:   operator@altcare.com / Operator@1234")
        print("\n📚 Geographic data:")
        print("  • 8 divisions, 64 districts, 495 upazilas")
        print("\n🔌 Integration providers:")
        print("  • SMS:     Twilio, Banglalink, Robi")
        print("  • Email:   SendGrid, AWS SES, SMTP")
        print("  • Payment: bKash, Nagad, Rocket, SSLCommerz, Stripe")
        print("\n💊 Medicines:")
        print("  • Homeopathy: Arnica, Belladonna, Nux Vomica, Pulsatilla, Rhus Tox")
        print("  • Ayurveda:   Ashwagandha, Triphala, Tulsi, Brahmi")
        print("  • Unani:      Kalonji, Senna")
        print("  • Herbal:     Turmeric, Ginger, Chamomile")
        print("\n🩺 Symptoms:")
        print("  • 25+ common symptoms across all categories")
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
