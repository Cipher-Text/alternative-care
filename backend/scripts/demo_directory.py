"""Public directory profiles for the three demo doctors (called from seed.py, development only).

Fills in everything a public profile shows (headline, bio in both languages, languages spoken, hours, fees, address,
map point, registration body, experience, degrees) and verifies the three clinics, so they appear on /practitioners.
The people, clinics, registration numbers and phone numbers are invented for the demo; the institutions in the degrees
are real ones from seed_data/institutions.json. Safe to run again: it sets the same values each time.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import DoctorDegree, Institution, PractitionerListing, Tenant, User

# district ids come from seed_data/geographic_data.json: 1 Dhaka, 49 Sylhet; 281 is Sylhet Sadar
DOCTORS = [
    dict(
        email="dr.rahman@example.com",
        tenant=dict(
            specializations=["homeopathy"],
            registration_body="Bangladesh Homeopathic Board",
            registration_number="H-DEMO-0412",
            years_of_experience=14,
            consultation_fee=80000,
            follow_up_fee=50000,
            clinic_phone="+8801700000101",
            clinic_whatsapp="+8801700000101",
            address_line_1="House 12, Road 8/A, Dhanmondi",
            address_line_2=None,
            landmark="Near Dhanmondi Lake, beside Star Kabab",
            postal_code="1209",
            district_id=1,
            upazila_id=None,
            latitude=23.7461,
            longitude=90.3742,
            description_en="A homeopathy clinic in Dhanmondi seeing adults and children for long-standing and recurring complaints.",
            description_bn="ধানমন্ডির একটি হোমিওপ্যাথি ক্লিনিক, যেখানে প্রাপ্তবয়স্ক ও শিশুদের পুরনো ও বারবার ফিরে আসা সমস্যার চিকিৎসা হয়।",
        ),
        listing=dict(
            headline_en="Classical homeopathy for chronic and recurring complaints",
            headline_bn="পুরনো ও বারবার ফিরে আসা রোগে ক্লাসিক্যাল হোমিওপ্যাথি",
            bio_en=(
                "I practise classical homeopathy with a long first consultation: about forty-five minutes to hear the whole "
                "story of the illness, the person and the family history before choosing a remedy. I see many patients with "
                "allergies and asthma, skin complaints, migraines, digestive problems and children's recurrent colds. "
                "Follow-ups are shorter and can be arranged by phone when a visit is difficult. I will tell you plainly when "
                "a condition needs a hospital or a specialist rather than homeopathy alone."
            ),
            bio_bn=(
                "আমি ক্লাসিক্যাল হোমিওপ্যাথি চর্চা করি। প্রথম সাক্ষাতে প্রায় পঁয়তাল্লিশ মিনিট সময় নিয়ে রোগের পুরো ইতিহাস, রোগীর স্বভাব "
                "ও পারিবারিক ইতিহাস শুনে তারপর ওষুধ বাছাই করি। অ্যালার্জি, হাঁপানি, চর্মরোগ, মাইগ্রেন, হজমের সমস্যা এবং শিশুদের বারবার "
                "সর্দি-কাশির রোগী বেশি আসেন। পরের সাক্ষাৎ ছোট হয়, আসা কঠিন হলে ফোনেও ঠিক করা যায়। যে রোগে হাসপাতাল বা বিশেষজ্ঞ দরকার, "
                "সেটা আমি স্পষ্ট করেই জানাই।"
            ),
            languages=["Bangla", "English"],
            consultation_hours="Sat to Thu, 4:00 pm to 9:00 pm. Friday closed. Appointment preferred.",
            availability="in_person",
        ),
        degrees=[
            dict(degree_type="DHMS", degree_name="Diploma in Homoeopathic Medicine and Surgery", institution="Government Homeopathic Medical College & Hospital", location="Mirpur, Dhaka", completed=2009, started=2004),
        ],
    ),
    dict(
        email="dr.karim@example.com",
        tenant=dict(
            specializations=["ayurveda", "herbal"],
            registration_body="Board of Unani and Ayurvedic Systems of Medicine, Bangladesh",
            registration_number="A-DEMO-1187",
            years_of_experience=11,
            consultation_fee=60000,
            follow_up_fee=40000,
            clinic_phone="+8801700000102",
            clinic_whatsapp="+8801700000102",
            address_line_1="Plot 5, Road 41, Gulshan 2",
            address_line_2=None,
            landmark="Opposite Gulshan 2 circle, second floor",
            postal_code="1212",
            district_id=1,
            upazila_id=None,
            latitude=23.7925,
            longitude=90.4078,
            description_en="An Ayurveda and herbal wellness centre in Gulshan focused on digestion, stress, sleep and lifestyle.",
            description_bn="গুলশানের একটি আয়ুর্বেদ ও ভেষজ স্বাস্থ্যকেন্দ্র, যেখানে হজম, মানসিক চাপ, ঘুম ও জীবনযাপনের সমস্যায় জোর দেওয়া হয়।",
        ),
        listing=dict(
            headline_en="Ayurveda for everyday wellness",
            headline_bn="প্রতিদিনের সুস্থতার জন্য আয়ুর্বেদ",
            bio_en=(
                "I work with Ayurvedic diet and routine advice, herbal formulations and simple home practices. Most of my "
                "patients come for digestive trouble, poor sleep, stress, joint stiffness and weight concerns. The first "
                "visit includes a detailed look at your daily habits, food and constitution, and I write down a plan you can "
                "follow at home. I use only herbal preparations from licensed manufacturers and explain every ingredient. "
                "Ayurveda is not a substitute for emergency care or for medicines your doctor has prescribed."
            ),
            bio_bn=(
                "আমি আয়ুর্বেদিক খাদ্য ও দৈনন্দিন রুটিনের পরামর্শ, ভেষজ ওষুধ এবং ঘরোয়া সহজ চর্চা নিয়ে কাজ করি। হজমের সমস্যা, কম ঘুম, "
                "মানসিক চাপ, জয়েন্টের আড়ষ্টতা ও ওজনের চিন্তা নিয়ে বেশি রোগী আসেন। প্রথম সাক্ষাতে আপনার দৈনন্দিন অভ্যাস, খাবার ও "
                "প্রকৃতি বিস্তারিত দেখে ঘরে মানার মতো একটি পরিকল্পনা লিখে দিই। শুধু লাইসেন্সপ্রাপ্ত প্রস্তুতকারকের ভেষজ ওষুধ ব্যবহার করি "
                "এবং প্রতিটি উপাদান বুঝিয়ে বলি। জরুরি চিকিৎসা বা আপনার ডাক্তারের দেওয়া ওষুধের বিকল্প আয়ুর্বেদ নয়।"
            ),
            languages=["Bangla", "English", "Hindi"],
            consultation_hours="Sun to Thu, 10:00 am to 2:00 pm and 5:00 pm to 8:00 pm. Saturday by appointment.",
            availability="both",
        ),
        degrees=[
            dict(degree_type="DAMS", degree_name="Diploma in Ayurvedic Medicine and Surgery", institution="Government Unani and Ayurvedic Medical College & Hospital", location="Dhaka", completed=2012, started=2007),
        ],
    ),
    dict(
        email="dr.listed@demo-clinic.example",
        tenant=dict(
            specializations=["herbal", "ayurveda"],
            registration_body="Board of Unani and Ayurvedic Systems of Medicine, Bangladesh",
            registration_number="A-DEMO-0634",
            years_of_experience=18,
            consultation_fee=50000,
            follow_up_fee=30000,
            clinic_phone="+8801700000103",
            clinic_whatsapp="+8801700000103",
            address_line_1="45 Zindabazar Main Road",
            address_line_2=None,
            landmark="Near Zindabazar Point, above the pharmacy",
            postal_code="3100",
            district_id=49,
            upazila_id=281,
            latitude=24.8949,
            longitude=91.8687,
            description_en="A herbal and Ayurvedic clinic in Sylhet town, practising for eighteen years.",
            description_bn="সিলেট শহরের একটি ভেষজ ও আয়ুর্বেদিক ক্লিনিক, আঠারো বছর ধরে চিকিৎসা দিচ্ছে।",
        ),
        listing=dict(
            headline_en="Herbal medicine for skin, joint and digestive complaints",
            headline_bn="ত্বক, জয়েন্ট ও হজমের সমস্যায় ভেষজ চিকিৎসা",
            bio_en=(
                "I have practised herbal and Ayurvedic medicine in Sylhet for eighteen years. I treat chronic skin conditions, "
                "joint pain, constipation and acidity, and I advise on seasonal diet. Patients often travel from the "
                "surrounding upazilas, so I keep a clear written plan for each person and answer follow-up questions by "
                "phone. I do not treat emergencies, and I refer patients with warning signs to the hospital."
            ),
            bio_bn=(
                "আমি আঠারো বছর ধরে সিলেটে ভেষজ ও আয়ুর্বেদিক চিকিৎসা দিচ্ছি। দীর্ঘস্থায়ী চর্মরোগ, জয়েন্টের ব্যথা, কোষ্ঠকাঠিন্য ও অ্যাসিডিটির "
                "চিকিৎসা করি এবং ঋতুভিত্তিক খাদ্যের পরামর্শ দিই। আশপাশের উপজেলা থেকে অনেক রোগী আসেন, তাই প্রত্যেকের জন্য স্পষ্ট লিখিত "
                "পরিকল্পনা রাখি এবং পরের প্রশ্নের উত্তর ফোনে দিই। জরুরি অবস্থার চিকিৎসা করি না; বিপদচিহ্ন থাকলে হাসপাতালে পাঠাই।"
            ),
            languages=["Bangla", "Sylheti", "English"],
            consultation_hours="Sat to Wed, 9:00 am to 1:00 pm and 4:00 pm to 8:00 pm. Thursday and Friday closed.",
            availability="in_person",
        ),
        degrees=[
            dict(degree_type="DAMS", degree_name="Diploma in Ayurvedic Medicine and Surgery", institution="Hamdard Institute of Unani and Ayurvedic Medicine", location="Dhaka", completed=2005, started=2000),
        ],
    ),
]


async def seed_demo_directory(session: AsyncSession) -> int:
    """Returns how many of the three profiles were filled in (0 if the demo doctors are not in this database)."""
    now = datetime.now(timezone.utc)
    done = 0
    for spec in DOCTORS:
        user = (await session.execute(select(User).where(User.email == spec["email"]))).scalar_one_or_none()
        if user is None or user.tenant_id is None:
            continue
        tenant = await session.get(Tenant, user.tenant_id)
        listing = (await session.execute(select(PractitionerListing).where(PractitionerListing.tenant_id == tenant.id))).scalar_one_or_none()
        if listing is None:
            continue

        for field, value in spec["tenant"].items():
            setattr(tenant, field, value)
        if not tenant.is_verified:
            tenant.is_verified = True
            tenant.verified_at = now
            tenant.verified_by = user.id  # a stand-in: the demo has no platform admin id here
        for field, value in spec["listing"].items():
            setattr(listing, field, value)
        listing.show_fee, listing.show_phone, listing.show_whatsapp, listing.accepts_requests = True, True, True, True
        listing.is_listed = True
        listing.listed_at = listing.listed_at or now

        has_degree = (await session.execute(select(DoctorDegree.id).where(DoctorDegree.user_id == user.id))).first()
        if has_degree is None:
            for order, degree in enumerate(spec["degrees"]):
                institution = (await session.execute(select(Institution).where(Institution.name_en == degree["institution"]))).scalars().first()
                session.add(
                    DoctorDegree(
                        tenant_id=tenant.id, user_id=user.id, degree_type=degree["degree_type"], degree_name=degree["degree_name"],
                        specialization=None, institution_name=degree["institution"], institution_location=degree["location"],
                        institution_id=institution.id if institution else None, start_year=degree["started"],
                        completion_year=degree["completed"], is_verified=True, verified_at=now, display_order=order,
                    )
                )
        done += 1
    await session.flush()
    return done
