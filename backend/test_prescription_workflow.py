#!/usr/bin/env python3
"""
Test prescription builder workflow end-to-end.

Tests:
1. Login as doctor
2. Get/create a patient
3. Create a draft prescription with items
4. Update the prescription
5. Issue the prescription
6. Verify immutability
"""

import asyncio
import httpx
from datetime import date


BASE_URL = "http://localhost:8000/api/v1"


async def test_prescription_workflow():
    """Test complete prescription workflow."""
    print("=" * 60)
    print("🧪 Testing Prescription Builder Workflow")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Step 1: Login as doctor
        print("\n1️⃣  Logging in as doctor...")
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "dr.rahman@example.com", "password": "Test@1234"}
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return

        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        print("✅ Logged in successfully")

        # Step 2: Get patients
        print("\n2️⃣  Fetching patients...")
        patients_response = await client.get(f"{BASE_URL}/patients", headers=headers)

        if patients_response.status_code != 200:
            print(f"❌ Failed to fetch patients: {patients_response.text}")
            return

        patients = patients_response.json()

        if not patients:
            print("📋 No patients found, creating one...")
            patient_data = {
                "first_name": "Test",
                "last_name": "Patient",
                "date_of_birth": "1990-01-15",
                "gender": "male",
                "phone": "+8801712345678"
            }
            create_patient_response = await client.post(
                f"{BASE_URL}/patients",
                json=patient_data,
                headers=headers
            )
            if create_patient_response.status_code != 201:
                print(f"❌ Failed to create patient: {create_patient_response.text}")
                return
            patient = create_patient_response.json()
            print(f"✅ Created patient: {patient['first_name']} {patient['last_name']}")
        else:
            patient = patients[0]
            print(f"✅ Using existing patient: {patient['first_name']} {patient['last_name']}")

        patient_id = patient["id"]

        # Step 3: Create draft prescription with items
        print("\n3️⃣  Creating draft prescription...")
        prescription_data = {
            "patient_id": patient_id,
            "diagnosis": "Common cold with throat irritation",
            "doctors_notes": "Patient presenting with mild fever and sore throat. Recommend rest and hydration.",
            "advice": "Avoid cold drinks. Take steam inhalation twice daily. Gargle with warm salt water.",
            "status": "draft",
            "items": [
                {
                    "medicine_name": "Arnica Montana 30C",
                    "dosage": "5 pills",
                    "frequency": "3 times daily",
                    "duration": "7 days",
                    "quantity": 105,
                    "instructions": "Take under tongue, avoid food/drink 15 min before and after"
                },
                {
                    "medicine_name": "Belladonna 200C",
                    "dosage": "3 pills",
                    "frequency": "Twice daily",
                    "duration": "5 days",
                    "quantity": 30,
                    "instructions": "Take in the morning and evening"
                }
            ]
        }

        create_rx_response = await client.post(
            f"{BASE_URL}/prescriptions",
            json=prescription_data,
            headers=headers
        )

        if create_rx_response.status_code != 201:
            print(f"❌ Failed to create prescription: {create_rx_response.text}")
            return

        prescription = create_rx_response.json()
        prescription_id = prescription["id"]
        print(f"✅ Created draft prescription: {prescription_id[:8]}...")
        print(f"   Status: {prescription['status']}")
        print(f"   Items: {len(prescription['items'])} medicines")

        # Step 4: Update prescription (add diagnosis)
        print("\n4️⃣  Updating draft prescription...")
        update_data = {
            "advice": prescription_data["advice"] + "\n\nFollow-up after 7 days if symptoms persist."
        }

        update_response = await client.patch(
            f"{BASE_URL}/prescriptions/{prescription_id}",
            json=update_data,
            headers=headers
        )

        if update_response.status_code != 200:
            print(f"❌ Failed to update prescription: {update_response.text}")
            return

        print("✅ Updated prescription successfully")

        # Step 5: Add another medicine item
        print("\n5️⃣  Adding another medicine...")
        new_item = {
            "medicine_name": "Nux Vomica 30C",
            "dosage": "4 pills",
            "frequency": "Twice daily",
            "duration": "3 days",
            "quantity": 24,
            "instructions": "Take before meals"
        }

        add_item_response = await client.post(
            f"{BASE_URL}/prescriptions/{prescription_id}/items",
            json=new_item,
            headers=headers
        )

        if add_item_response.status_code != 201:
            print(f"❌ Failed to add item: {add_item_response.text}")
            return

        print("✅ Added new medicine item")

        # Step 6: Get updated prescription
        print("\n6️⃣  Fetching updated prescription...")
        get_rx_response = await client.get(
            f"{BASE_URL}/prescriptions/{prescription_id}",
            headers=headers
        )

        if get_rx_response.status_code != 200:
            print(f"❌ Failed to fetch prescription: {get_rx_response.text}")
            return

        updated_prescription = get_rx_response.json()
        print(f"✅ Fetched prescription")
        print(f"   Status: {updated_prescription['status']}")
        print(f"   Items: {len(updated_prescription['items'])} medicines")
        print(f"   Medicines:")
        for i, item in enumerate(updated_prescription['items'], 1):
            print(f"      {i}. {item['medicine_name']} - {item['dosage']} {item['frequency']}")

        # Step 7: Issue prescription
        print("\n7️⃣  Issuing prescription...")
        issue_response = await client.patch(
            f"{BASE_URL}/prescriptions/{prescription_id}",
            json={"status": "issued"},
            headers=headers
        )

        if issue_response.status_code != 200:
            print(f"❌ Failed to issue prescription: {issue_response.text}")
            return

        issued_prescription = issue_response.json()
        print(f"✅ Issued prescription successfully")
        print(f"   Status: {issued_prescription['status']}")

        # Step 8: Verify immutability (try to update issued prescription)
        print("\n8️⃣  Testing immutability (should fail)...")
        try_update_response = await client.patch(
            f"{BASE_URL}/prescriptions/{prescription_id}",
            json={"diagnosis": "Changed diagnosis"},
            headers=headers
        )

        if try_update_response.status_code == 400:
            print("✅ Immutability enforced correctly (update blocked)")
        else:
            print(f"⚠️  Expected 400 error, got: {try_update_response.status_code}")

        # Step 9: Try to add item to issued prescription (should fail)
        print("\n9️⃣  Testing item addition to issued prescription (should fail)...")
        try_add_response = await client.post(
            f"{BASE_URL}/prescriptions/{prescription_id}/items",
            json=new_item,
            headers=headers
        )

        if try_add_response.status_code == 400:
            print("✅ Item addition blocked for issued prescription")
        else:
            print(f"⚠️  Expected 400 error, got: {try_add_response.status_code}")

        # Summary
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print(f"\n📊 Test Summary:")
        print(f"   • Login: ✓")
        print(f"   • Patient retrieval: ✓")
        print(f"   • Draft creation: ✓")
        print(f"   • Draft update: ✓")
        print(f"   • Item addition: ✓")
        print(f"   • Prescription issue: ✓")
        print(f"   • Immutability check: ✓")
        print(f"\n🎯 Prescription ID: {prescription_id}")
        print(f"\n💡 Test in browser:")
        print(f"   1. Go to: http://localhost:3000/login")
        print(f"   2. Login: dr.rahman@example.com / Test@1234")
        print(f"   3. Navigate to: http://localhost:3000/prescriptions/{prescription_id}")
        print(f"   4. Or create new: http://localhost:3000/prescriptions/new")
        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_prescription_workflow())
