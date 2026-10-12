# Health history field review

Review document for one practising doctor per system (homeopathy, Ayurveda, Unani). Sent before the system-specific case-taking screens are built (step 3 of the plan after step 1, which added the shared vitals and health profile). Bengali wording is a draft.

Reply by ID, for example `H12 drop; A3 change: add "variable"`. Rows flagged **(check term)** are the author's least certain terms.

## Already built for every system

- **Vitals at every visit** (প্রতিটি ভিজিটে ভাইটাল): Temperature, pulse, blood pressure, breathing rate, oxygen saturation, weight, height (BMI is worked out), blood sugar and when it was taken, pain score 0–10.
- **Warning signs and referral** (সতর্ক লক্ষণ ও রেফার): Chest pain, breathlessness, severe bleeding, high fever in an infant, loss of consciousness, sudden severe headache, sudden weakness, persistent vomiting. Referral: none, routine, urgent, emergency.
- **Health background** (স্বাস্থ্যের পটভূমি): Long-term conditions, allergies (drug, food, herb, dust or pollen, skin contact, insect) with severity, family history, smoking, alcohol, paan/jorda/gul, diet, pregnancy and last period, breastfeeding, allopathic medicines, blood thinners, recent surgery.
- **Safety banner** (সতর্কতা বার্তা): Before prescribing, the screen shows allergy, pregnancy, breastfeeding, age under 5 or over 65, other medicines, blood thinners, recent surgery, and the long-term conditions.

## Homeopathy (হোমিওপ্যাথি)

Case-taking built around the whole person: the complaint with its modalities, then physical generals, the mind, the patient's history, and tracking of each remedy given.

### Complaint in detail (অভিযোগের বিস্তারিত)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| H1 | Location / স্থান | Write |  |
| H2 | Sensation / অনুভূতির ধরন | Tick any | `burning`: Burning / জ্বালাপোড়া; `stitching`: Stitching / ছুঁচ ফোটানোর মতো; `throbbing`: Throbbing / দপদপ; `cutting`: Cutting / কাটার মতো; `pressing`: Pressing / চাপ দেওয়ার মতো; `cramping`: Cramping / খিঁচুনি; `tearing`: Tearing / ছেঁড়ার মতো; `bursting`: Bursting / ফেটে যাওয়ার মতো; `dull`: Dull / ভোঁতা; `sharp`: Sharp / তীক্ষ্ণ; `itching`: Itching / চুলকানি; `numbness`: Numbness / অবশ ভাব |
| H3 | Onset / শুরু | Choose one | `sudden`: Sudden / হঠাৎ; `gradual`: Gradual / ধীরে ধীরে |
| H4 | Duration / কতদিন ধরে | Number | `days`: Days / দিন; `weeks`: Weeks / সপ্তাহ; `months`: Months / মাস; `years`: Years / বছর |
| H5 | Illness began after (causation) / যার পর থেকে অসুস্থতা শুরু | Tick any | `grief`: Grief / শোক; `fright`: Fright / ভয়; `anger`: Anger / রাগ; `shock`: Shock / মানসিক আঘাত; `suppressed_emotion`: Suppressed emotion / চাপা আবেগ; `injury`: Injury / আঘাত; `vaccination`: Vaccination / টিকা; `suppressed_discharge`: Suppressed skin disease or discharge / চাপা পড়া চর্মরোগ বা স্রাব; `cold_wet`: Exposure to cold or wet / ঠান্ডা বা ভেজা; `overwork`: Overwork / অতিরিক্ত পরিশ্রম; `after_illness`: After fever or another illness / জ্বর বা অন্য অসুখের পর |
| H6 | Worse from / যাতে বাড়ে | Tick any | `morning`: Morning / সকাল; `afternoon`: Afternoon / বিকাল; `evening`: Evening / সন্ধ্যা; `night`: Night / রাত; `heat`: Heat / গরম; `cold`: Cold / ঠান্ডা; `damp`: Damp weather / স্যাঁতসেঁতে আবহাওয়া; `weather_change`: Change of weather / আবহাওয়া বদল; `motion`: Motion / নড়াচড়া; `rest`: Rest / বিশ্রাম; `lying_left`: Lying on the left / বাম কাতে শোয়া; `lying_right`: Lying on the right / ডান কাতে শোয়া; `touch`: Touch / স্পর্শ; `pressure`: Pressure / চাপ; `eating`: Eating / খাওয়া; `drinking`: Drinking / পানি পান; `sleep`: Sleep / ঘুম; `company`: Company / মানুষের সঙ্গ; `solitude`: Being alone / একা থাকা |
| H7 | Better from / যাতে কমে | Tick any | `morning`: Morning / সকাল; `afternoon`: Afternoon / বিকাল; `evening`: Evening / সন্ধ্যা; `night`: Night / রাত; `heat`: Heat / গরম; `cold`: Cold / ঠান্ডা; `damp`: Damp weather / স্যাঁতসেঁতে আবহাওয়া; `weather_change`: Change of weather / আবহাওয়া বদল; `motion`: Motion / নড়াচড়া; `rest`: Rest / বিশ্রাম; `lying_left`: Lying on the left / বাম কাতে শোয়া; `lying_right`: Lying on the right / ডান কাতে শোয়া; `touch`: Touch / স্পর্শ; `pressure`: Pressure / চাপ; `eating`: Eating / খাওয়া; `drinking`: Drinking / পানি পান; `sleep`: Sleep / ঘুম; `company`: Company / মানুষের সঙ্গ; `solitude`: Being alone / একা থাকা |
| H8 | Accompanying symptoms / সঙ্গের উপসর্গ | Write |  |
| H9 | Side affected / কোন দিকে | Choose one | `right`: Right / ডান; `left`: Left / বাম; `both`: Both / দুই দিকে; `alternating`: Alternating / পালা করে |

### Physical generals (শারীরিক সাধারণ লক্ষণ)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| H10 | Thermal state / শীত-গরমের ধাত | Choose one | `chilly`: Chilly / শীতকাতর; `hot`: Hot / গরমকাতর; `ambithermal`: In between / মাঝামাঝি |
| H11 | Thirst / পিপাসা | Choose one | `thirstless`: Thirstless / তৃষ্ণাহীন; `little`: Little / অল্প; `moderate`: Moderate / মাঝারি; `large`: Large / প্রচুর |
| H12 | Water preference / পানির পছন্দ | Choose one | `cold`: Cold / ঠান্ডা; `warm`: Warm / গরম; `none`: No preference / কোনো পছন্দ নেই |
| H13 | Food desires / খাবারের আকাঙ্ক্ষা | Tick any | `sweet`: Sweet / মিষ্টি; `salty`: Salty / নোনতা; `sour`: Sour / টক; `spicy`: Spicy / ঝাল; `fatty`: Fatty or fried / চর্বি বা ভাজা; `milk`: Milk / দুধ; `eggs`: Eggs / ডিম; `meat`: Meat / মাংস; `fish`: Fish / মাছ; `cold_drinks`: Cold drinks / ঠান্ডা পানীয়; `hot_drinks`: Hot drinks / গরম পানীয় |
| H14 | Food aversions / যে খাবারে অরুচি | Tick any | `sweet`: Sweet / মিষ্টি; `salty`: Salty / নোনতা; `sour`: Sour / টক; `spicy`: Spicy / ঝাল; `fatty`: Fatty or fried / চর্বি বা ভাজা; `milk`: Milk / দুধ; `eggs`: Eggs / ডিম; `meat`: Meat / মাংস; `fish`: Fish / মাছ; `cold_drinks`: Cold drinks / ঠান্ডা পানীয়; `hot_drinks`: Hot drinks / গরম পানীয় |
| H15 | Perspiration / ঘাম | Choose one | `none`: None / নেই; `scanty`: Scanty / সামান্য; `moderate`: Moderate / মাঝারি; `profuse`: Profuse / প্রচুর |
| H16 | Perspiration odour / ঘামের গন্ধ | Choose one | `none`: None / নেই; `offensive`: Offensive / দুর্গন্ধযুক্ত |
| H17 | Perspiration — where / ঘাম কোথায় | Write |  |
| H18 | Sleep position / ঘুমের ভঙ্গি | Choose one | `back`: On the back / চিত; `left`: Left side / বাম কাত; `right`: Right side / ডান কাত; `abdomen`: On the abdomen / উপুড়; `any`: No fixed position / নির্দিষ্ট নেই |
| H19 | Dreams / স্বপ্ন | Write |  |
| H20 | Menstrual cycle / মাসিকের চক্র | Choose one | `regular`: Regular / নিয়মিত; `irregular`: Irregular / অনিয়মিত |
| H21 | Menstrual flow / মাসিকের প্রবাহ | Choose one | `scanty`: Scanty / কম; `normal`: Normal / স্বাভাবিক; `heavy`: Heavy / বেশি |
| H22 | Menstrual pain / মাসিকের ব্যথা | Choose one | `none`: None / নেই; `before`: Before / আগে; `during`: During / চলাকালীন; `after`: After / পরে |
| H23 | Leucorrhoea / সাদা স্রাব | Choose one | `none`: None / নেই; `mild`: Mild / অল্প; `profuse`: Profuse / প্রচুর |

### Mind (মন)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| H24 | Fears / ভয় | Tick any | `dark`: Dark / অন্ধকার; `alone`: Being alone / একা থাকা; `death`: Death / মৃত্যু; `disease`: Disease / রোগ; `animals`: Animals / প্রাণী; `heights`: Heights / উচ্চতা; `crowd`: Crowds / ভিড়; `exams`: Exams / পরীক্ষা |
| H25 | Mood tendencies / মেজাজের প্রবণতা | Tick any | `anxious`: Anxious / দুশ্চিন্তাগ্রস্ত; `irritable`: Irritable / খিটখিটে; `weepy`: Weepy / কান্নাপ্রবণ; `sad`: Sad / বিষণ্ণ; `restless`: Restless / অস্থির; `suspicious`: Suspicious / সন্দেহপ্রবণ; `jealous`: Jealous / ঈর্ষাপ্রবণ; `indifferent`: Indifferent / উদাসীন; `cheerful`: Cheerful / হাসিখুশি |
| H26 | Effect of consolation / সান্ত্বনার প্রভাব | Choose one | `better`: Better / ভালো লাগে; `worse`: Worse / খারাপ লাগে; `none`: No effect / কোনো প্রভাব নেই |
| H27 | Company / সঙ্গ | Choose one | `desire`: Desires company / সঙ্গ চান; `aversion`: Dislikes company / সঙ্গ অপছন্দ; `none`: No effect / কোনো প্রভাব নেই |

### History and constitution (ইতিহাস ও গঠন)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| H28 | Childhood illnesses / শৈশবের অসুখ | Tick any | `measles`: Measles / হাম; `chickenpox`: Chickenpox / জলবসন্ত; `mumps`: Mumps / মাম্পস; `whooping_cough`: Whooping cough / হুপিং কাশি; `typhoid`: Typhoid / টাইফয়েড; `jaundice`: Jaundice / জন্ডিস; `tonsillitis`: Recurrent tonsillitis / বারবার টনসিলাইটিস; `worms`: Worms / কৃমি |
| H29 | Earlier suppressive treatment / আগের চাপা দেওয়া চিকিৎসা | Tick any | `steroid_cream`: Steroid creams / স্টেরয়েড ক্রিম; `antibiotics`: Repeated antibiotics / বারবার অ্যান্টিবায়োটিক; `antihistamines`: Antihistamines / অ্যান্টিহিস্টামিন; `painkillers`: Long-term painkillers / দীর্ঘদিন ব্যথানাশক; `vaccine_reaction`: Reaction after vaccination / টিকার পর প্রতিক্রিয়া |
| H30 | Earlier homeopathic remedies and response / আগের হোমিও ওষুধ ও সাড়া | List of rows | `remedy`: Remedy / ওষুধ; `potency`: Potency / শক্তি; `response`: Better, same or worse / ভালো, একই বা খারাপ |
| H31 | Dominant miasm (optional) / প্রধান মায়াজম (ঐচ্ছিক) **(check term)** | Choose one | `psora`: Psora / সোরা; `sycosis`: Sycosis / সাইকোসিস; `syphilis`: Syphilis / সিফিলিস; `tubercular`: Tubercular / টিউবারকুলার |

### Prescription and follow-up (প্রেসক্রিপশন ও ফলো-আপ)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| H32 | Remedy / ওষুধ | Write |  |
| H33 | Potency / শক্তি | Choose one | `6c`: 6C / ৬সি; `30c`: 30C / ৩০সি; `200c`: 200C / ২০০সি; `1m`: 1M / ১এম; `10m`: 10M / ১০এম; `lm`: LM scale / এলএম; `mt`: Mother tincture / মাদার টিংচার |
| H34 | Dose form / ডোজের ধরন | Choose one | `pills`: Pills / বড়ি; `liquid`: Liquid / তরল; `powder`: Powder / পাউডার; `tablet`: Tablet / ট্যাবলেট |
| H35 | Repetition / কতবার | Choose one | `single`: Single dose / একবারই; `daily`: Daily / প্রতিদিন; `twice_daily`: Twice a day / দিনে দুবার; `weekly`: Weekly / সপ্তাহে একবার; `as_needed`: As needed / প্রয়োজনমতো |
| H36 | Things to avoid / যা এড়াতে হবে | Tick any | `coffee`: Coffee / কফি; `camphor`: Camphor / কর্পূর; `mint`: Mint / পুদিনা; `strong_smells`: Strong smells / তীব্র গন্ধ |
| H37 | Response at follow-up / ফলো-আপে সাড়া | Choose one | `better`: Better / ভালো; `same`: Same / একই; `worse`: Worse / খারাপ; `aggravation_then_better`: Worse first, then better / প্রথমে বাড়ে, পরে কমে; `new_symptom`: New symptom / নতুন উপসর্গ |
| H38 | Next step / পরবর্তী সিদ্ধান্ত | Choose one | `continue`: Continue the same / একই চালিয়ে যান; `change_potency`: Change the potency / শক্তি বদলান; `change_remedy`: Change the remedy / ওষুধ বদলান; `wait`: Wait / অপেক্ষা করুন |

## Ayurveda (আয়ুর্বেদ)

Assessment of the constitution (prakriti) and the present imbalance (vikriti), digestive fire, the eight-fold examination, the causes, and the treatment with its vehicle and diet.

### Constitution and imbalance (প্রকৃতি ও বিকৃতি)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| A1 | Prakriti (born constitution) / প্রকৃতি | Choose one | `vata`: Vata / বাত; `pitta`: Pitta / পিত্ত; `kapha`: Kapha / কফ; `vata_pitta`: Vata-pitta / বাত-পিত্ত; `pitta_kapha`: Pitta-kapha / পিত্ত-কফ; `vata_kapha`: Vata-kapha / বাত-কফ; `tridosha`: All three equal / সমদোষ |
| A2 | Vikriti (present imbalance) / বিকৃতি | Choose one | `vata`: Vata / বাত; `pitta`: Pitta / পিত্ত; `kapha`: Kapha / কফ; `vata_pitta`: Vata-pitta / বাত-পিত্ত; `pitta_kapha`: Pitta-kapha / পিত্ত-কফ; `vata_kapha`: Vata-kapha / বাত-কফ; `tridosha`: All three / ত্রিদোষ |
| A3 | Agni (digestive fire) / অগ্নি | Choose one | `sama`: Balanced (sama) / সম; `vishama`: Irregular (vishama) / বিষম; `tikshna`: Sharp (tikshna) / তীক্ষ্ণ; `manda`: Slow (manda) / মন্দ |
| A4 | Koshtha (bowel type) / কোষ্ঠ | Choose one | `mridu`: Soft (mridu) / মৃদু; `madhyama`: Medium (madhyama) / মধ্যম; `krura`: Hard (krura) / ক্রূর |
| A5 | Ama (undigested residue) / আম | Choose one | `absent`: Absent / নেই; `mild`: Mild / সামান্য; `moderate`: Moderate / মাঝারি; `marked`: Marked / বেশি |

### Ashtavidha pariksha (eight-fold examination) (অষ্টবিধ পরীক্ষা)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| A6 | Nadi (pulse) / নাড়ি | Choose one | `vata`: Vata type / বাত; `pitta`: Pitta type / পিত্ত; `kapha`: Kapha type / কফ; `mixed`: Mixed / মিশ্র |
| A7 | Mutra (urine) / মূত্র | Tick any | `normal`: Normal / স্বাভাবিক; `increased`: Increased / বেশি; `reduced`: Reduced / কম; `burning`: Burning / জ্বালাপোড়া; `turbid`: Turbid / ঘোলা; `frequent_night`: Frequent at night / রাতে বারবার |
| A8 | Mala (stool) / মল | Choose one | `normal`: Normal / স্বাভাবিক; `hard`: Hard / শক্ত; `loose`: Loose / পাতলা; `sticky`: Sticky / আঠালো; `undigested`: With undigested food / অজীর্ণ খাবারসহ |
| A9 | Jihva (tongue) / জিহ্বা | Choose one | `clean`: Clean / পরিষ্কার; `white`: White coating / সাদা আস্তরণ; `yellow`: Yellow coating / হলুদ আস্তরণ; `thick`: Thick coating / পুরু আস্তরণ; `cracked`: Cracked / ফাটা; `red`: Red / লালচে |
| A10 | Shabda (voice) / শব্দ / স্বর | Choose one | `normal`: Normal / স্বাভাবিক; `hoarse`: Hoarse / ভাঙা; `weak`: Weak / দুর্বল; `loud`: Loud / জোরালো |
| A11 | Sparsha (touch, skin) / স্পর্শ | Tick any | `warm`: Warm / উষ্ণ; `cool`: Cool / শীতল; `dry`: Dry / শুষ্ক; `oily`: Oily / তৈলাক্ত; `rough`: Rough / খসখসে; `moist`: Moist / আর্দ্র |
| A12 | Drik (eyes) / দৃক / চোখ | Tick any | `normal`: Normal / স্বাভাবিক; `dull`: Dull / নিষ্প্রভ; `red`: Red / লাল; `yellowish`: Yellowish / হলদেটে; `dry`: Dry / শুষ্ক; `watery`: Watery / জলযুক্ত |
| A13 | Akriti (build) / আকৃতি | Choose one | `thin`: Thin / কৃশ; `medium`: Medium / মাঝারি; `heavy`: Heavy / স্থূল |

### Strength and capacity (optional, from dashavidha pariksha) (বল ও সক্ষমতা (ঐচ্ছিক))

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| A14 | Bala (strength) / বল **(check term)** | Choose one | `good`: Good / ভালো; `medium`: Medium / মাঝারি; `poor`: Poor / কম |
| A15 | Satva (mental strength) / সত্ত্ব **(check term)** | Choose one | `strong`: Strong / প্রবল; `medium`: Medium / মাঝারি; `weak`: Weak / দুর্বল |
| A16 | Ahara shakti (digestive capacity) / আহারশক্তি **(check term)** | Choose one | `good`: Good / ভালো; `medium`: Medium / মাঝারি; `poor`: Poor / কম |
| A17 | Vyayama shakti (exercise capacity) / ব্যায়ামশক্তি **(check term)** | Choose one | `good`: Good / ভালো; `medium`: Medium / মাঝারি; `poor`: Poor / কম |
| A18 | Vaya (age stage) / বয়স | Choose one | `bala`: Child (bala) / বাল; `madhya`: Adult (madhya) / মধ্য; `vriddha`: Elderly (vriddha) / বৃদ্ধ |
| A19 | Preferred tastes / পছন্দের স্বাদ | Tick any | `madhura`: Sweet (madhura) / মধুর; `amla`: Sour (amla) / অম্ল; `lavana`: Salty (lavana) / লবণ; `katu`: Pungent (katu) / কটু; `tikta`: Bitter (tikta) / তিক্ত; `kashaya`: Astringent (kashaya) / কষায় |

### Cause and disease process (নিদান ও সম্প্রাপ্তি)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| A20 | Nidana (causes) / নিদান | Tick any | `improper_diet`: Improper diet / অনুচিত খাদ্য; `irregular_meals`: Irregular meals / অনিয়মিত খাওয়া; `day_sleep`: Sleeping in the day / দিনে ঘুম; `night_waking`: Staying awake at night / রাত জাগা; `suppressed_urges`: Suppressing natural urges / বেগ ধারণ; `stress`: Stress / মানসিক চাপ; `too_much_exercise`: Too much exercise / অতিরিক্ত ব্যায়াম; `too_little_exercise`: Too little exercise / ব্যায়ামের অভাব; `seasonal`: Seasonal / ঋতুজনিত |
| A21 | Doshas involved / দূষিত দোষ | Tick any | `vata`: Vata / বাত; `pitta`: Pitta / পিত্ত; `kapha`: Kapha / কফ |
| A22 | Dhatus involved / দূষিত ধাতু | Tick any | `rasa`: Rasa / রস; `rakta`: Rakta / রক্ত; `mamsa`: Mamsa / মাংস; `meda`: Meda / মেদ; `asthi`: Asthi / অস্থি; `majja`: Majja / মজ্জা; `shukra`: Shukra / শুক্র |
| A23 | Srotas involved / স্রোতস **(check term)** | Tick any | `pranavaha`: Pranavaha (breath) / প্রাণবহ; `annavaha`: Annavaha (food) / অন্নবহ; `udakavaha`: Udakavaha (water) / উদকবহ; `rasavaha`: Rasavaha / রসবহ; `raktavaha`: Raktavaha / রক্তবহ; `mamsavaha`: Mamsavaha / মাংসবহ; `medovaha`: Medovaha / মেদোবহ; `asthivaha`: Asthivaha / অস্থিবহ; `majjavaha`: Majjavaha / মজ্জাবহ; `shukravaha`: Shukravaha / শুক্রবহ; `mutravaha`: Mutravaha / মূত্রবহ; `purishavaha`: Purishavaha / পুরীষবহ; `svedavaha`: Svedavaha / স্বেদবহ; `artavavaha`: Artavavaha / আর্তববহ; `manovaha`: Manovaha / মনোবহ |
| A24 | Desha (region type) / দেশ **(check term)** | Choose one | `anupa`: Marshy, wet (anupa) / আনূপ; `jangala`: Dry (jangala) / জাঙ্গল; `sadharana`: Mixed (sadharana) / সাধারণ |
| A25 | Ritu (season) / ঋতু | Choose one | `vasanta`: Spring / বসন্ত; `grishma`: Summer / গ্রীষ্ম; `varsha`: Rains / বর্ষা; `sharad`: Autumn / শরৎ; `hemanta`: Late autumn / হেমন্ত; `shishira`: Winter / শীত |

### Treatment (চিকিৎসা)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| A26 | Treatment approach / চিকিৎসার ধরন | Choose one | `shamana`: Pacifying (shamana) / শমন; `shodhana`: Purifying (shodhana) / শোধন; `both`: Both / উভয় |
| A27 | Panchakarma advised or done / পঞ্চকর্ম | Tick any | `vamana`: Vamana / বমন; `virechana`: Virechana / বিরেচন; `basti`: Basti / বস্তি; `nasya`: Nasya / নস্য; `raktamokshana`: Raktamokshana / রক্তমোক্ষণ |
| A28 | Formulation / ওষুধ / যোগ | Write |  |
| A29 | Anupana (vehicle) / অনুপান | Choose one | `warm_water`: Warm water / কুসুম গরম পানি; `honey`: Honey / মধু; `ghee`: Ghee / ঘি; `milk`: Milk / দুধ; `buttermilk`: Buttermilk / ঘোল; `other`: Other / অন্যান্য |
| A30 | When to take / কখন খাবেন | Choose one | `before_food`: Before food / খাবারের আগে; `after_food`: After food / খাবারের পরে; `empty_stomach`: Empty stomach / খালি পেটে; `bedtime`: At bedtime / শোয়ার আগে |
| A31 | Diet and lifestyle advice / পথ্য ও জীবনযাপনের পরামর্শ | Write |  |
| A32 | Metal-based (rasa-shastra) preparations taken before / আগে ধাতুঘটিত (রসশাস্ত্র) ওষুধ খেয়েছেন | Choose one | `yes`: Yes / হ্যাঁ; `no`: No / না; `unknown`: Not known / জানা নেই |

## Unani (ইউনানী)

Assessment of temperament (mizaj), the humours (akhlat), the six essential factors of life, pulse, urine and stool, and treatment by regimen, diet and drugs.

### Temperament and humours (মিজাজ ও আখলাত)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| U1 | Mizaj (temperament) / মিজাজ **(check term)** | Choose one | `damvi`: Sanguine (damvi) / দামাভী (রক্তপ্রধান); `balghami`: Phlegmatic (balghami) / বালগামী (কফপ্রধান); `safravi`: Choleric (safravi) / সাফরাভী (পিত্তপ্রধান); `saudavi`: Melancholic (saudavi) / সাওদাভী (কৃষ্ণপিত্তপ্রধান) |
| U2 | Mizaj of the disease / রোগের মিজাজ **(check term)** | Choose one | `hot_dry`: Hot and dry / উষ্ণ-শুষ্ক; `hot_moist`: Hot and moist / উষ্ণ-আর্দ্র; `cold_dry`: Cold and dry / শীতল-শুষ্ক; `cold_moist`: Cold and moist / শীতল-আর্দ্র |
| U3 | Akhlat (humours) affected / আখলাত **(check term)** | Tick any | `dam`: Dam (blood) / দম (রক্ত); `balgham`: Balgham (phlegm) / বালগাম (কফ); `safra`: Safra (yellow bile) / সাফরা (পিত্ত); `sauda`: Sauda (black bile) / সাওদা (কৃষ্ণপিত্ত) |

### Examination (পরীক্ষা)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| U4 | Nabz (pulse) — rate per minute / নাবজ — প্রতি মিনিটে | Number |  |
| U5 | Nabz (pulse) — character / নাবজের ধরন **(check term)** | Tick any | `strong`: Strong / সবল; `weak`: Weak / দুর্বল; `fast`: Fast / দ্রুত; `slow`: Slow / ধীর; `full`: Full / পূর্ণ; `empty`: Empty / ফাঁপা; `hard`: Hard / কঠিন; `soft`: Soft / নরম; `irregular`: Irregular / অনিয়মিত |
| U6 | Baul (urine) — colour / বাউল (প্রস্রাব) — রং **(check term)** | Choose one | `pale`: Pale / ফ্যাকাশে; `straw`: Straw / খড়ের রং; `yellow`: Yellow / হলুদ; `dark`: Dark or reddish / গাঢ় বা লালচে |
| U7 | Baul (urine) — clarity / বাউল — স্বচ্ছতা **(check term)** | Choose one | `clear`: Clear / স্বচ্ছ; `turbid`: Turbid / ঘোলা; `sediment`: With sediment / তলানিসহ |
| U8 | Baraz (stool) / বারাজ (মল) **(check term)** | Choose one | `normal`: Normal / স্বাভাবিক; `hard`: Hard / শক্ত; `loose`: Loose / পাতলা; `mucous`: With mucus / আমযুক্ত; `pale`: Pale / ফ্যাকাশে; `dark`: Dark / কালচে |
| U9 | Skin and complexion / ত্বক ও গাত্রবর্ণ **(check term)** | Choose one | `pale`: Pale / ফ্যাকাশে; `ruddy`: Ruddy / রক্তিম; `yellowish`: Yellowish / হলদেটে; `dusky`: Dusky / কালচে |
| U10 | Tongue / জিহ্বা | Choose one | `clean`: Clean / পরিষ্কার; `white`: White coating / সাদা আস্তরণ; `yellow`: Yellow coating / হলুদ আস্তরণ; `dry`: Dry / শুষ্ক |
| U11 | Lams (examination by touch) — notes / লামস — নোট | Write |  |

### Asbab-e-sitta zaruriya (six essential factors) (আসবাব-এ-সিত্তা জরুরিয়া (ছয়টি অপরিহার্য কারণ))

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| U12 | Hawa-e-muhit (air and surroundings) / হাওয়া-এ-মুহিত (পরিবেশের বাতাস) **(check term)** | Choose one | `normal`: Normal / স্বাভাবিক; `excess`: Too much / বেশি; `deficient`: Too little / কম; `abnormal`: Abnormal quality / অস্বাভাবিক |
| U13 | Makool-o-mashroob (food and drink) / মাকুল-ও-মাশরুব (খাদ্য ও পানীয়) **(check term)** | Choose one | `normal`: Normal / স্বাভাবিক; `excess`: Too much / বেশি; `deficient`: Too little / কম; `abnormal`: Abnormal quality / অস্বাভাবিক |
| U14 | Harkat-o-sukoon badni (physical activity and rest) / হারকত-ও-সুকুন বাদনী (শারীরিক পরিশ্রম ও বিশ্রাম) **(check term)** | Choose one | `normal`: Normal / স্বাভাবিক; `excess`: Too much / বেশি; `deficient`: Too little / কম; `abnormal`: Abnormal quality / অস্বাভাবিক |
| U15 | Harkat-o-sukoon nafsani (mental activity and rest) / হারকত-ও-সুকুন নাফসানী (মানসিক ক্রিয়া ও বিশ্রাম) **(check term)** | Choose one | `normal`: Normal / স্বাভাবিক; `excess`: Too much / বেশি; `deficient`: Too little / কম; `abnormal`: Abnormal quality / অস্বাভাবিক |
| U16 | Naum-o-yaqza (sleep and wakefulness) / নওম-ও-ইয়াকজা (ঘুম ও জাগরণ) **(check term)** | Choose one | `normal`: Normal / স্বাভাবিক; `excess`: Too much / বেশি; `deficient`: Too little / কম; `abnormal`: Abnormal quality / অস্বাভাবিক |
| U17 | Ehtebas-o-istifragh (retention and evacuation) / ইহতিবাস-ও-ইস্তিফরাগ (ধারণ ও নিষ্কাশন) **(check term)** | Choose one | `normal`: Normal / স্বাভাবিক; `excess`: Too much / বেশি; `deficient`: Too little / কম; `abnormal`: Abnormal quality / অস্বাভাবিক |

### Treatment (চিকিৎসা)

| ID | Field | Type | Choices (code: English / বাংলা) |
|---|---|---|---|
| U18 | Ilaj bil tadbeer (regimenal therapy) / ইলাজ বিল তদবীর **(check term)** | Tick any | `hijama`: Cupping (hijama) / হিজামা; `fasd`: Venesection (fasd) / ফাসদ; `dalk`: Massage (dalk) / দালক; `hammam`: Bath (hammam) / হাম্মাম; `riyazat`: Exercise (riyazat) / রিয়াযত; `taleeq`: Leeching (taleeq) / তালিক (জোঁক); `ishal`: Purgation (ishal) / ইশহাল; `qai`: Emesis (qai) / কায়; `huqna`: Enema (huqna) / হুকনা; `idrar`: Diuresis (idrar) / ইদরার |
| U19 | Ilaj bil ghiza (dietotherapy) — advice / ইলাজ বিল গিযা (পথ্য) — পরামর্শ | Write |  |
| U20 | Ilaj bil dawa — drug / ইলাজ বিল দাওয়া — ওষুধ | Write |  |
| U21 | Drug type / ওষুধের ধরন **(check term)** | Choose one | `mufrad`: Single drug (mufrad) / মুফরাদ (একক); `murakkab`: Compound (murakkab) / মুরাক্কাব (যৌগিক) |
| U22 | Drug form / ওষুধের রূপ **(check term)** | Choose one | `safoof`: Powder (safoof) / সফুফ (গুঁড়া); `joshanda`: Decoction (joshanda) / জোশান্দা; `sharbat`: Syrup (sharbat) / শরবত; `majoon`: Majoon / মাজুন; `qurs`: Tablet (qurs) / কুরস (ট্যাবলেট); `marham`: Ointment (marham) / মারহাম (মলম); `roghan`: Oil (roghan) / রওগন (তেল); `arq`: Distillate (arq) / আরক; `khamira`: Khamira / খামিরা |
| U23 | Mizaj and degree of the drug (shown from the medicine library) / ওষুধের মিজাজ ও দরজা (ওষুধ-তালিকা থেকে দেখাবে) **(check term)** | Write |  |

## Questions for every reviewer

1. Which five or six fields do you use in almost every consultation? / কোন পাঁচ-ছয়টি ঘর আপনি প্রায় প্রতিটি রোগীর জন্য ব্যবহার করেন?
2. Which fields would you never fill in, or fill in only for a few patients? / কোন ঘরগুলো আপনি কখনোই পূরণ করেন না, বা শুধু কয়েকজন রোগীর জন্য করেন?
3. Which terms are wrong, spelt differently in your school, or have a better Bengali name? / কোন শব্দ ভুল, আপনার ঘরানায় ভিন্নভাবে লেখা হয়, বা বাংলায় আরও ভালো নাম আছে?
4. What do you write on every patient's card that is not here? / প্রতিটি রোগীর কার্ডে আপনি এমন কী লেখেন যা এখানে নেই?
5. Which choices in a list are missing, and which should be removed? / কোন তালিকায় কোন বিকল্প নেই, আর কোনটি বাদ দেওয়া উচিত?
