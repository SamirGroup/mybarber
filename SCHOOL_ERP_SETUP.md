# SCHOOL ERP MODULI - O'RNATISH VA ISHGA TUSHIRISH

## 1. MIGRATSIYALARNI YARATISH VA BAJARISH

```bash
# Migratsiyalarni yaratish
python manage.py makemigrations students

# Migratsiyalarni bajarish
python manage.py migrate students
```

## 2. DEMO MA'LUMOTLARNI YUKLASH

```bash
# Students moduli uchun demo ma'lumotlar
python manage.py seed_students_data

# Agar mavjud ma'lumotlarni o'chirib, qaytadan yuklash kerak bo'lsa:
python manage.py seed_students_data --reset
```

## 3. ADMIN PANEL ORQALI KIRISH

1. Superuser yarating (agar yo'q bo'lsa):
```bash
python manage.py createsuperuser
```

2. Admin panelga kiring: http://localhost:8000/admin/

3. Students bo'limida quyidagi modellarni ko'rasiz:
   - Classrooms (Sinf xonalari)
   - Students (O'quvchilar)
   - Parents (Ota-onalar)
   - Subjects (Fanlar)
   - Schedules (Dars jadvali)
   - Daily Grades (Kunlik baholar)
   - Quarter Grades (Chorak baholari)
   - Attendance (Davomat)
   - Homework (Uy vazifalari)
   - Contracts (Shartnomalar)
   - Payments (To'lovlar)
   - Chat Groups (Chat guruhlar)
   - Document Types (Hujjat turlari)

## 4. FOYDALANUVCHI GURUHLARINI YARATISH

Students modulida ishlash uchun quyidagi guruhlarni yarating:

1. Admin panelda: Authentication and Authorization → Groups
2. Yangi guruh yarating:
   - `students_agent` - Oddiy xodimlar uchun
   - `students_manager` - Menejerlar uchun

3. Foydalanuvchilarni guruhlarga qo'shing

## 5. ASOSIY URL MANZILLAR

- Dashboard: http://localhost:8000/students/
- O'quvchilar ro'yxati: http://localhost:8000/students/list/
- Sinf xonalari: http://localhost:8000/students/classrooms/
- Dars jadvali: http://localhost:8000/students/schedule/
- Uy vazifalari: http://localhost:8000/students/homework/
- Fanlar: http://localhost:8000/students/subjects/
- SMS sozlamalari: http://localhost:8000/students/sms/config/
- Chat: http://localhost:8000/students/chat/

## 6. MODULNING ASOSIY FUNKSIYALARI

### 6.1 O'quvchilar boshqaruvi
- O'quvchilarni ro'yxatga olish
- Shaxsiy ma'lumotlarni saqlash
- Ota-onalar bilan bog'lash
- Sinflarga biriktirish
- Hujjatlarni yuklash

### 6.2 Darslar va jadval
- Fanlar ro'yxati
- Dars jadvali tuzish
- O'qituvchilarni biriktrish
- Sinf xonalarini boshqarish

### 6.3 Baholar va davomat
- Kunlik baholar qo'yish
- Chorak baholari
- Davomat belgilash
- Natijalarni ko'rish

### 6.4 Uy vazifalari
- Uy vazifalarini yaratish
- Fayllarni yuklash
- Topshirish muddatini belgilash

### 6.5 Moliya
- Shartnomalar tuzish
- To'lovlarni qabul qilish
- Qarzdorlikni hisoblash
- To'lov tarixini ko'rish

### 6.6 SMS xabarnomalar
- Avtomatik SMS yuborish
- Qarzdorlar uchun eslatmalar
- SMS shablonlarini sozlash
- SMS loglarini ko'rish

### 6.7 Ichki chat
- Guruh chatlari
- Sinf bo'yicha chatlar
- Fayl yuborish
- Xabarlar tarixi

### 6.8 Hujjatlar
- Hujjat turlarini belgilash
- Fayllarni yuklash
- Majburiy hujjatlarni belgilash

## 7. CALL CENTRE BILAN INTEGRATSIYA

Students moduli enrollment (Call Centre) moduli bilan integratsiyalashgan:

1. Lead (Lid) dan Student (O'quvchi) ga o'tkazish
2. Ota-onalar ma'lumotlarini avtomatik ko'chirish
3. API orqali o'quvchi yaratish

### API Endpoint:
```
POST /students/api/add-student/
```

### Request body:
```json
{
  "phone": "+998901234567",
  "first_name": "Alisher",
  "last_name": "Aliyev",
  "email": "alisher@example.com",
  "child_first_name": "Ali",
  "child_last_name": "Aliyev",
  "birth_date": "2015-05-20",
  "gender": "M",
  "lead_id": 123
}
```

## 8. TEMPLATE FAYLLAR

Barcha template fayllar `templates/students/` papkasida joylashgan:
- dashboard.html
- student_list.html
- student_detail.html
- student_form.html
- classroom_list.html
- classroom_detail.html
- homework_list.html
- payment_form.html
- sms_config.html
- chat_detail.html
- va boshqalar...

## 9. XAVFSIZLIK

- Barcha view'lar `@login_required` dekorator bilan himoyalangan
- Faqat `students_agent` yoki `students_manager` guruhidagi foydalanuvchilar kirishi mumkin
- Superuser barcha funksiyalarga kirish huquqiga ega

## 10. KELAJAKDA QILISH KERAK BO'LGAN ISHLAR

- [ ] Real SMS gateway integratsiyasi (Twilio, Playmobile, Eskiz.uz)
- [ ] Hujjatlarni PDF formatda generatsiya qilish
- [ ] Excel export funksiyasi
- [ ] Baholar statistikasi va grafiklar
- [ ] Ota-onalar uchun mobil ilova API
- [ ] WebSocket orqali real-time chat
- [ ] Email xabarnomalar
- [ ] Biometrik davomat tizimi integratsiyasi

## 11. MUAMMOLARNI HAL QILISH

### Agar migratsiya xatolari bo'lsa:
```bash
python manage.py migrate students --fake-initial
```

### Agar demo ma'lumotlar yuklanmasa:
```bash
python manage.py seed_students_data --reset
```

### Agar static fayllar ko'rinmasa:
```bash
python manage.py collectstatic --noinput
```

## 12. QULAYLIKLAR

- Barcha formalar O'zbek tilida
- Intuitiv interfeys
- Tez qidiruv va filtrlash
- Responsive dizayn (mobil qurilmalar uchun)
- Pagination (sahifalash)
- Avtomatik hisob-kitoblar

## 13. TEXNIK TALABLAR

- Python 3.8+
- Django 4.0+
- PostgreSQL yoki SQLite
- Redis (chat uchun, ixtiyoriy)
- Celery (SMS uchun, ixtiyoriy)

## 14. YORDAM VA QO'LLAB-QUVVATLASH

Savollar bo'lsa, quyidagi fayllarni ko'rib chiqing:
- `students/models.py` - Ma'lumotlar bazasi modellari
- `students/views.py` - Business logika
- `students/admin.py` - Admin panel konfiguratsiyasi
- `students/urls.py` - URL marshrutlari

---

**Muvaffaqiyatli ishlar tilaymiz! 🎓**
