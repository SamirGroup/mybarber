# SCHOOL ERP MODULI - TEZKOR BOSHLASH

## ✅ MUVAFFAQIYATLI O'RNATILDI!

Demo ma'lumotlar muvaffaqiyatli yuklandi. Endi quyidagi qadamlarni bajaring:

## 1. SERVERNI ISHGA TUSHIRING

```bash
python manage.py runserver
```

## 2. ADMIN PANELGA KIRING

URL: http://localhost:8000/admin/

Login: (sizning superuser ma'lumotlaringiz)

## 3. STUDENTS MODULINI OCHISH

Brauzerda quyidagi URL'larni oching:

### Asosiy sahifalar:
- **Dashboard**: http://localhost:8000/students/
- **O'quvchilar**: http://localhost:8000/students/list/
- **Sinf xonalari**: http://localhost:8000/students/classrooms/
- **Fanlar**: http://localhost:8000/students/subjects/
- **Dars jadvali**: http://localhost:8000/students/schedule/
- **Uy vazifalari**: http://localhost:8000/students/homework/

### Moliya:
- **To'lovlar**: Har bir o'quvchi sahifasida
- **Shartnomalar**: Har bir o'quvchi sahifasida

### SMS:
- **SMS sozlamalari**: http://localhost:8000/students/sms/config/
- **SMS loglar**: http://localhost:8000/students/sms/logs/

### Chat:
- **Chat guruhlar**: http://localhost:8000/students/chat/

## 4. DEMO MA'LUMOTLAR

Quyidagi demo ma'lumotlar yaratildi:

### O'quvchilar: 15 ta
- Ali Aliyev
- Kamila Karimova
- Timur Toshmatov
- Ruxsora Rahimova
- Yusuf Yusupov
- va boshqalar...

### Ota-onalar: 10 ta
- Telefon raqamlari: +998901234567 dan boshlanadi

### Sinf xonalari: 12 ta
- 1-A, 1-B
- 2-A, 2-B
- 3-A, 3-B
- 4-A, 4-B
- 5-A, 5-B
- 6-A, 6-B

### Fanlar: 10 ta
- Matematika
- Ona tili
- Ingliz tili
- Fizika
- Kimyo
- Biologiya
- Tarix
- Geografiya
- Informatika
- Jismoniy tarbiya

### Shartnomalar: 10 ta
- Oylik to'lov: 500,000 so'm
- Shartnoma raqamlari: 2024-1000 dan boshlanadi

### To'lovlar: 8 ta
- Naqd to'lovlar
- Joriy oy uchun

### Dars jadvali: 60 ta
- Dushanba-Juma
- 08:00 dan 13:45 gacha

### Baholar:
- Kunlik baholar: 50 ta
- Chorak baholari: 100 ta

### Davomat: 70 ta
- Oxirgi 7 kun uchun

### Uy vazifalari: 9 ta
- Har xil fanlar bo'yicha

### Hujjat turlari: 5 ta
- Pasport nusxasi
- Tug'ilganlik haqida guvohnoma
- Tibbiy ma'lumotnoma
- 3x4 fotosurat
- Oldingi maktab ma'lumotnomasi

### Chat guruhlar: 2 ta
- 1-A ota-onalar guruhi
- 1-B ota-onalar guruhi

## 5. FOYDALANUVCHI GURUHLARINI YARATISH

Admin panelda:

1. **Groups** bo'limiga o'ting
2. Yangi guruh yarating: `students_agent`
3. Yangi guruh yarating: `students_manager`
4. O'zingizni `students_manager` guruhiga qo'shing

## 6. ASOSIY FUNKSIYALARNI SINAB KO'RING

### O'quvchi qo'shish:
1. http://localhost:8000/students/new/ ga o'ting
2. Formani to'ldiring
3. Saqlang

### To'lov qabul qilish:
1. O'quvchi sahifasiga o'ting
2. "To'lov qo'shish" tugmasini bosing
3. Summani kiriting
4. Saqlang

### Baholar qo'yish:
1. http://localhost:8000/students/grades/daily/ ga o'ting
2. O'quvchi va fanni tanlang
3. Bahoni kiriting
4. Saqlang

### Davomat belgilash:
1. http://localhost:8000/students/attendance/ ga o'ting
2. O'quvchi va sanani tanlang
3. Holatni tanlang (Keldi/Kelmadi/Kech keldi)
4. Saqlang

### Uy vazifasi yaratish:
1. http://localhost:8000/students/homework/new/ ga o'ting
2. Sinf va fanni tanlang
3. Sarlavha va tavsifni kiriting
4. Topshirish muddatini belgilang
5. Saqlang

### SMS yuborish:
1. http://localhost:8000/students/sms/config/ ga o'ting
2. Sozlamalarni o'zgartiring
3. "SMS yuborish" tugmasini bosing
4. Loglarni ko'ring: http://localhost:8000/students/sms/logs/

## 7. CALL CENTRE BILAN INTEGRATSIYA

Enrollment modulidan o'quvchi yaratish:

1. Lead yarating: http://localhost:8000/enrollment/leads/new/
2. Lead sahifasida "O'quvchiga aylantirish" tugmasini bosing
3. Students modulida yangi o'quvchi paydo bo'ladi

## 8. KEYINGI QADAMLAR

- [ ] Template fayllarni dizayn qiling
- [ ] Real SMS gateway ulang (Eskiz.uz, Playmobile)
- [ ] PDF generatorni qo'shing
- [ ] Excel export qo'shing
- [ ] Statistika va grafiklar qo'shing
- [ ] Mobil ilova API yarating

## 9. YORDAM

Agar muammo bo'lsa:

1. Loglarni tekshiring
2. Admin panelda ma'lumotlarni ko'ring
3. Database'ni tekshiring: `python manage.py dbshell`

## 10. QULAYLIKLAR

✅ To'liq CRUD operatsiyalar
✅ Qidiruv va filtrlash
✅ Pagination
✅ Avtomatik hisob-kitoblar
✅ SMS xabarnomalar
✅ Ichki chat
✅ Hujjatlar yuklash
✅ Moliya boshqaruvi
✅ Baholar va davomat
✅ Dars jadvali

---

**Muvaffaqiyatli ishlar! 🎓📚**
