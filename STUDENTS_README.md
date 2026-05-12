# O'quvchilar Bo'limi - Xususiy Maktab Tizimi

## 📋 Umumiy Ma'lumot

Bu xususiy maktab uchun to'liq o'quvchilar boshqaruv tizimi. Tizim quyidagi funksiyalarni o'z ichiga oladi:

## ✅ Asosiy Funksiyalar

### 1. Sinf Boshqaruvi
- Sinf yaratish (1-A, 5-B va h.k.)
- Sinf rahbari tayinlash
- O'quvchilar soni va sig'imni kuzatish
- Dars jadvali boshqaruvi

### 2. O'quvchi Ma'lumotlari
- **Shaxsiy ma'lumotlar:**
  - Ism, familiya, otasining ismi
  - Jinsi, tug'ilgan sana, yoshi
  - Metrika yoki ID karta raqami
  - ERP maktab tizimidagi raqam
  - Manzil, tibbiy eslatmalar

- **Ota-ona ma'lumotlari:**
  - Bir ota-onada bir necha farzand
  - Telefon raqamlar (2 tagacha)
  - Email manzil
  - Aloqa turi (Ota/Ona/Vasiy)

### 3. Hujjatlar Tizimi
- 0 dan hujjat turlarini yaratish
- Hujjat yuklash (PDF, Word, rasm)
- Hujjat turlari:
  - Tug'ilganlik haqida guvohnoma
  - Pasport nusxasi
  - Tibbiy ma'lumotnoma
  - Tabel
  - Oldingi maktab ma'lumotnomasi
  - Va boshqalar...

### 4. Dars Jadvali
- Haftalik dars jadvali
- Fanlar va o'qituvchilar
- Dars vaqtlari
- Avtomatik o'quvchiga biriktiriladi

### 5. Baholash Tizimi
- **Kunlik baholar:**
  - Har bir fan bo'yicha
  - Izoh qo'shish imkoniyati
  - Sana bo'yicha kuzatish

- **Chorak baholari:**
  - 4 ta chorak
  - Fan bo'yicha yakuniy baho
  - O'qituvchi tomonidan kiritiladi

### 6. Davomat
- Kunlik davomat
- Statuslar: Keldi, Kelmadi, Kech keldi, Uzrli
- Fan bo'yicha davomat
- Eslatmalar

### 7. Uy Vazifalar
- O'qituvchi tomonidan yaratiladi
- Sinf yoki alohida o'quvchilarga
- Fayl biriktirish
- Deadline belgilash
- Tavsif va izohlar

### 8. Ichki Chat Tizimi
- O'qituvchi chat guruh yaratadi
- Alohida o'quvchilarni biriktirish
- Butun sinfni biriktirish
- Real-time xabarlar
- Fayl yuborish
- Admin panelida barcha xabarlar ko'rinadi

### 9. Moliya Tizimi
- **Shartnomalar:**
  - Shartnoma raqami
  - Oylik to'lov
  - Chegirma (foiz va sabab)
  - Muddat (boshlanish/tugash)
  - Haqiqiy to'lov (chegirma hisobga olingan)

- **To'lovlar:**
  - Naqd, karta, o'tkazma
  - Qaysi oy uchun to'lov
  - To'lov tarixi
  - Balans hisoblash

- **Qarzdorlik:**
  - Avtomatik hisoblash
  - Ota-ona bo'yicha guruhlash
  - Bir ota-onada bir necha farzand hisobga olinadi

### 10. SMS Xabarnoma Tizimi
- **Avtomatik SMS:**
  - Har oyning belgilangan kunida
  - Faqat qarzdor ota-onalarga
  - Bir ota-onaga bitta SMS (barcha farzandlar uchun)
  
- **SMS shabloni:**
  ```
  Hurmatli {parent_name}! Farzandingiz {student_name} uchun 
  {contract_number} shartnoma bo'yicha {debt_amount} so'm 
  qarzdorlik mavjud. Iltimos, to'lovni amalga oshiring.
  ```

- **SMS sozlamalari:**
  - Har oyning qaysi kunida yuborilsin
  - Faol/nofaol qilish
  - Shablon tahrirlash
  - SMS tarixi

## 🚀 Ishga Tushirish

### 1. Migration larni bajarish:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Demo ma'lumotlarni yuklash:
```bash
python manage.py seed_students_data
```

### 3. Serverni ishga tushirish:
```bash
python manage.py runserver
```

## 📊 URL lar

### Asosiy sahifalar:
- `/students/` - Dashboard
- `/students/list/` - O'quvchilar ro'yxati
- `/students/new/` - Yangi o'quvchi
- `/students/<id>/` - O'quvchi profili

### Sinflar:
- `/students/classrooms/` - Sinf xonalari
- `/students/classrooms/new/` - Yangi sinf
- `/students/classrooms/<id>/` - Sinf tafsilotlari

### Uy vazifalar:
- `/students/homework/` - Uy vazifalar ro'yxati
- `/students/homework/new/` - Yangi uy vazifa

### Chat:
- `/students/chat/` - Chat guruhlar
- `/students/chat/new/` - Yangi chat guruh
- `/students/chat/<id>/` - Chat xonasi

### Moliya:
- `/students/<id>/finance/` - O'quvchi moliyasi
- `/students/<id>/payment/add/` - To'lov qo'shish
- `/students/<id>/contract/add/` - Shartnoma yaratish

### SMS:
- `/students/sms/config/` - SMS sozlamalari
- `/students/sms/send-now/` - Hozir SMS yuborish
- `/students/sms/logs/` - SMS tarixi

### Boshqalar:
- `/students/subjects/` - Fanlar
- `/students/document-types/` - Hujjat turlari
- `/students/schedule/` - Dars jadvali
- `/students/grades/daily/` - Kunlik baholar
- `/students/grades/quarter/` - Chorak baholari
- `/students/attendance/` - Davomat

## 👥 Foydalanuvchi Rollari

### students_agent
- O'quvchilarni ko'rish
- Baholar kiritish
- Davomat belgilash
- Uy vazifa yaratish
- Chat guruhlar yaratish

### students_manager
- Barcha students_agent huquqlari
- O'quvchi yaratish/tahrirlash
- Sinf yaratish
- Shartnoma yaratish
- To'lov qabul qilish
- SMS yuborish

### enrollment_agent / enrollment_manager
- Students bo'limiga kirish huquqi
- O'quvchilarni ko'rish
- Qabul qilish jarayonidan o'quvchi yaratish

## 📱 SMS Integratsiya

SMS yuborish uchun Twilio yoki mahalliy SMS gateway ishlatiladi:

```python
# settings.py da sozlash
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = '+998901234567'
```

## 🔒 Xavfsizlik

- Barcha sahifalar login talab qiladi
- Role-based access control (RBAC)
- Hujjatlar faqat ruxsat berilgan foydalanuvchilarga
- SMS faqat qarzdorlar uchun
- Chat xabarlari admin tomonidan kuzatiladi

## 📈 Hisobotlar

Dashboard da ko'rsatiladigan statistika:
- Jami o'quvchilar
- Faol o'quvchilar
- Sinf xonalari soni
- Faol shartnomalar
- Qarzdorlar ro'yxati
- So'nggi to'lovlar
- Uy vazifalar

## 🎯 Xususiyatlar

1. **Sinf kesimida tartibla** - O'quvchilarni sinf bo'yicha filter qilish
2. **Choraklar bo'yicha natijalar** - Har bir chorak uchun alohida baholar
3. **Sort qilish** - Ism, familiya, sinf, sana bo'yicha
4. **Qidirish** - Ism, metrika, ERP raqam bo'yicha
5. **Batafsil profil** - Barcha ma'lumotlar bir sahifada
6. **Tab interfeysi** - Ma'lumotlar, hujjatlar, baholar, davomat, moliya, uy vazifalar, chat

## 🛠️ Texnologiyalar

- Django 6.0+
- SQLite (development) / PostgreSQL (production)
- Bootstrap 5
- Font Awesome 6
- Chart.js (grafik lar uchun)
- Twilio (SMS uchun)

## 📞 Qo'llab-quvvatlash

Savollar yoki muammolar bo'lsa:
1. GitHub Issues
2. Email: support@example.com
3. Telegram: @support

## 📝 Litsenziya

MIT License

---

**Eslatma:** Bu tizim xususiy maktablar uchun maxsus ishlab chiqilgan va barcha O'zbekiston ta'lim standartlariga mos keladi.