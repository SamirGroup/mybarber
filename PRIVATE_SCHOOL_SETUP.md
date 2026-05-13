# Xususiy Maktab ERP Tizimi - To'liq O'rnatish Qo'llanmasi

## Umumiy Tavsif

Bu tizim xususiy maktablar uchun mo'ljallangan bo'lib, quyidagi bo'limlarni o'z ichiga oladi:

1. **Qabul (Reception/Enrollment)** - Meta Lead orqali arizalar qabul qilish
2. **Call Centre** - O'zbekiston telefon kompaniyalari (Ucell, Beeline, Umnitel) uchun moslashtirilgan
3. **O'quvchilar (Students)** - To'liq o'quvchilar boshqaruvi

---

## 1. Qabul Bo'limi (Reception)

### Meta Lead Integratsiyasi

Meta (Facebook/Instagram) dan avtomatik lead'larni qabul qilish:

```python
# Environment variables (.env faylga qo'shing):
META_VERIFY_TOKEN=bunyod_school_2025
META_APP_SECRET=your_app_secret
META_ACCESS_TOKEN=your_long_lived_token
META_LEAD_FETCH_ENABLED=True
META_LEAD_AUTO_ASSIGN_FIRST_AGENT=True
```

**Webhook URL:** `https://your-domain.com/enrollment/webhook/meta-lead/`

**Qo'llab-quvvatlanadigan maydonlar:**
- Telefon raqam (majburiy)
- Ota-onaning ismi
- Bolaning ismi
- Sinf (Grade)
- Viloyat/Shahar
- Bolalar soni
- Chegirma ma'lumoti

**Chegirma avtomatik hisoblash:**
- 2+ bola = 10% chegirma
- 3+ bola = 20% chegirma

---

## 2. Call Centre (O'zbekiston Telefon Kompaniyalari)

### Twilio Integratsiyasi

```python
# Environment variables:
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_API_KEY=your_api_key
TWILIO_API_SECRET=your_api_secret
TWILIO_PHONE_NUMBER=+998901234567
CALL_CENTER_AGENT_NUMBER=+998901234567
```

### O'zbekiston Operatorlari Dasturiy Ta'minoti

Tizim quyidagi operatorlarni avtomatik aniqlaydi:

| Kod | Operator |
|-----|----------|
| 90  | Ucell    |
| 91  | Beeline  |
| 93  | Ucell    |
| 94  | Beeline  |
| 95  | Umnitel (UMC) |
| 97  | Beeline  |
| 98  | Ucell    |
| 99  | Beeline  |

### Telefon Raqam Normalizatsiyasi

```python
# CallRecord modelida:
call.normalize_phone_uzbekistan('901234567')  # → '+998901234567'
call.normalize_phone_uzbekistan('998901234567')  # → '+998901234567'
call.normalize_phone_uzbekistan('+998901234567')  # → '+998901234567'
```

### Qo'ng'iroq Xususiyatlari

- ✅ Kiruvchi va chiquvchi qo'ng'iroqlar
- ✅ Qo'ng'iroq yozuvi (Recording)
- ✅ Agent statusi (Online/Offline/Break)
- ✅ Qo'ng'iroq navbati (Queue)
- ✅ Avtomatik lead biriktirish
- ✅ O'zbekcha ovozli xabarlar

**TwiML O'zbekcha Xabar:**
```xml
<Say language="uz-UZ">Xususiy Maktab qabul bo'limiga xush kelibsiz. Iltimos, kuting, operator siz bilan bog'lanadi.</Say>
```

---

## 3. O'quvchilar Bo'limi (Students)

### Sinf Xonalari (Classrooms)

**Yaratish:**
- Sinf nomi (masalan: "5-A", "6-B")
- Grade (Grade 1, Grade 2, ...)
- Akademik yil
- Sinf rahbari (Homeroom Teacher)
- Sig'imi (Capacity)

### O'quvchi Ma'lumotlari

**Asosiy ma'lumotlar:**
- Ism, Familiya, Otasining ismi
- Jinsi
- Tug'ilgan sana (avtomatik yosh hisoblash)
- Metrika yoki ID karta raqami
- ERP maktab raqami
- Photo
- Sinf
- Ota-ona ma'lumotlari
- Manzil
- Tibbiy eslatmalar

**Hujjatlar (0 dan cheksiz):**
- Ma'lumotnoma
- Tabel
- Pasport nusxasi
- Tibbiy kartochka
- Oldingi maktabdan arayez
- va boshqalar...

### Baholar Tizimi

**Kunlik baholar (Daily Grades):**
- Har bir dars uchun baho
- Comment qo'shish
- Sana va fan tanlash

**Chorak baholar (Quarter Grades):**
- 1, 2, 3, 4-chorak
- Har bir fan uchun
- O'rtacha baho avtomatik hisoblash

**Natijalar:**
```python
student.get_quarter_grades_by_subject(quarter)  # Fanlar bo'yicha baholar
student.get_average_grade()  # Umumiy o'rtacha baho
```

### Davomat (Attendance)

**Statuslar:**
- Keldi (Present)
- Kelmadi (Absent)
- Kech keldi (Late)
- Uzrli (Excused)

**Davomat foizi:**
```python
student.get_attendance_rate()  # 30 kunlik davomat %
```

### Uy Vazifalari (Homework)

**O'qituvchi:**
- Uy vazifasi yaratish
- Butun sinfga yoki alohida o'quvchilarga
- Fayl biriktirish
- Muddat belgilash

**O'quvchi:**
- Uy vazifasini ko'rish
- Topshirish (text yoki fayl)
- Baho va izoh ko'rish

### Chat Tizimi

**Guruh turlari:**
- Sinf guruhi
- Fan guruhi
- Maxsus guruh

**Imkoniyatlar:**
- Xabar yuborish/o'qish
- Fayl biriktirish
- O'qilgan/o'qilmagan status
- Edit/Delete xabar

### Chegirmalar

**Chegirma ko'rsatish:**
```python
student.has_discount  # Chegirma bormi?
student.total_discount  # Jami chegirma %
student.get_discount_details()  # Batafsil ma'lumot
```

**Chegirma sabablari:**
- Ko'p bolali oila
- Ijtimoiy himoyaga muhtoj
- A'lochi o'quvchi
- Maxsus taklif
- va boshqalar...

### Moliya (Finance)

**Shartnoma:**
- Shartnoma raqami
- Oylik to'lov miqdori
- Chegirma % va sababi
- Boshlanish va tugash sanasi
- Aktiv/Passiv holati

**To'lovlar:**
- Har oy uchun avtomatik yaratish
- To'lov uslubi (Naqd/Karta/O'tkazma)
- Qarzdorlik avtomatik hisoblash

**Balans:**
```python
balance = student.get_balance_for_month(year, month)
# {
#   'total_debt': 500000,
#   'total_paid': 1500000,
#   'expected': 2000000
# }
```

### SMS Xabarnomalar

**Sozlamalar:**
```python
SmsNotificationConfig:
- day_of_month: 5  # Har oyning 5-kuni
- is_active: True
- message_template: "Hurmatli {parent_name}! Farzandingiz {student_name} uchun..."
```

**Avtomatik yuborish:**
```bash
# Cron job yoki Celery task:
curl -X POST https://your-domain.com/students/sms/daily-task/
```

**SMS logi:**
- Kimga yuborildi
- Qachon yuborildi
- Xabar matni
- Qarz miqdori
- Yuborilgan holati

---

## O'rnatish Qadamlari

### 1. Environment Variables

`.env` faylini yaratish:

```env
# Database
DATABASE_URL=sqlite:///db.sqlite3

# Secret Key
SECRET_KEY=your-secret-key-here

# Debug
DEBUG=True

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_API_KEY=your_api_key
TWILIO_API_SECRET=your_api_secret
TWILIO_PHONE_NUMBER=+998901234567
CALL_CENTER_AGENT_NUMBER=+998901234567

# Meta (Facebook)
META_VERIFY_TOKEN=bunyod_school_2025
META_APP_SECRET=your_app_secret
META_ACCESS_TOKEN=your_long_lived_token
META_LEAD_FETCH_ENABLED=True
META_LEAD_AUTO_ASSIGN_FIRST_AGENT=True

# Redis (Celery)
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Timezone
TIME_ZONE=Asia/Tashkent
```

### 2. Dependencies Install

```bash
pip install -r requirements.txt
```

### 3. Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Superuser Create

```bash
python manage.py createsuperuser
```

### 5. Run Server

```bash
python manage.py runserver
```

---

## API Endpoints

### Qabul (Enrollment)

- `POST /enrollment/webhook/meta-lead/` - Meta Lead webhook
- `POST /enrollment/call/initiate/` - Qo'ng'iroq boshlash
- `POST /enrollment/call/end/` - Qo'ng'iroq tugatish
- `GET /enrollment/api/customer-info/?phone=+998901234567` - Mijoz ma'lumotlari

### O'quvchilar (Students)

- `POST /students/sms/send-now/` - SMS yuborish
- `POST /students/sms/daily-task/` - Kunlik SMS task
- `GET /students/api/student/<id>/` - O'quvchi ma'lumotlari

---

## Foydalanuvchi Guruhlari

### Enrollment (Qabul)

- `enrollment_agent` - Leadlar bilan ishlash, qo'ng'iroq qilish
- `enrollment_manager` - Barcha imkoniyatlar + hisobotlar

### Students (O'quvchilar)

- `students_agent` - O'quvchilar, baholar, davomat
- `students_manager` - Barcha imkoniyatlar + moliya

---

## Hisobotlar

### Call Centre

- Kunlik qo'ng'iroqlar soni
- Javob berilgan/berilmagan
- O'rtacha muloqot vaqti
- Agent statistikasi

### O'quvchilar

- Umumiy o'quvchilar soni
- Har bir sinfdagi o'quvchilar
- Davomat foizi
- O'rtacha baholar
- Qarzdorlar ro'yxati

### Moliya

- Oylik to'lovlar
- Qarzdorlik jami
- Chegirmalar hisobi

---

## Qo'shimcha Xususiyatlar

### O'quvchini Ko'chirish (Transfer)

- Sinf o'zgartirish
- Maktabdan chiqarish
- Tamomlash
- Tarix saqlash

### Audit Log

- Barcha muhim harakatlar yoziladi
- Kim, nima, qachon o'zgartirdi
- Qo'ng'iroq yozuvlari kirish

### Multi-language

- O'zbek (Latin)
- O'zbek (Kirill)
- Rus

---

## Texnik Support

Agar muammo bo'lsa:
1. Django logs tekshiring
2. Environment variables to'g'riligini tasdiqlang
3. Database migrations yangiligini tekshiring
4. Redis ishlashini tekshiring (agar Celery ishlatilsa)

---

## Xavfsizlik

- Barcha API endpointlar CSRF protection
- Foydalanuvchi autentifikatsiyasi majburiy
- Telefon raqamlari mask qilinadi (ixtiyoriy)
- Qo'ng'iroq yozuvlari shifrlangan
- Audit log barcha harakatlar uchun

---

**Version:** 1.0  
**Last Updated:** 2025  
**Author:** NLP-Core-Team
