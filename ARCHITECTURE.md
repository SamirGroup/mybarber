# LOYIHANING UMUMIY ARXITEKTURASI

## 1. TIZIM ARXITEKTURASI

```
┌─────────────────────────────────────────────────────────────────┐
│                     YAGONA DJANGO PLATFORMA                      │
│                     (Bakery ERP + School ERP)                    │
├─────────────────────────────┬───────────────────────────────────┤
│   CALL CENTRE MODULI         │      SCHOOL ERP MODULI            │
│   (enrollment app)           │      (students app)               │
├─────────────────────────────┼───────────────────────────────────┤
│ • Lead Management            │ • O'quvchilar boshqaruvi          │
│ • Call Recording (Twilio)    │ • Sinf xonalari                   │
│ • Agent Dashboard            │ • Darslar va jadval               │
│ • Meta Lead Integration      │ • Baholar va davomat              │
│ • Application Processing     │ • Uy vazifalari                   │
│ • Call Queue                 │ • To'lovlar va shartnomalar       │
│ • Call Routing               │ • SMS xabarnomalar                │
│ • Agent Profiles             │ • Ichki chat tizimi               │
│ • Audit Logs                 │ • Hujjatlar boshqaruvi            │
│                              │ • Ota-onalar bilan aloqa          │
└─────────────────────────────┴───────────────────────────────────┘
```

## 2. MA'LUMOTLAR BAZASI MODELLARI

### ENROLLMENT APP (Call Centre)
```
Lead
├── LeadSource
├── Grade
├── AcademicYear
├── LeadStatusHistory
├── LeadComment
└── CallRecord
    ├── CallCampaign
    ├── CallQueue
    ├── CallRouting
    └── AgentProfile

StudentApplication
├── Lead (FK)
└── Grade (FK)

AuditLog
CallStatistics
```

### STUDENTS APP (School ERP)
```
Student
├── Classroom
│   ├── Grade (FK)
│   ├── AcademicYear (FK)
│   └── homeroom_teacher (User FK)
├── Parent (M2M)
└── Documents
    └── DocumentType

Academic
├── Subject
├── Schedule
│   ├── Classroom (FK)
│   ├── Subject (FK)
│   └── Teacher (User FK)
├── Quarter
│   └── AcademicYear (FK)
├── DailyGrade
│   ├── Student (FK)
│   ├── Subject (FK)
│   └── Teacher (User FK)
└── QuarterGrade
    ├── Student (FK)
    ├── Subject (FK)
    ├── Quarter (FK)
    └── Teacher (User FK)

Attendance
├── Student (FK)
├── Subject (FK)
└── marked_by (User FK)

Homework
├── Classroom (FK)
├── Subject (FK)
└── Teacher (User FK)

Finance
├── Contract
│   └── Student (FK)
└── Payment
    ├── Student (FK)
    ├── Contract (FK)
    └── received_by (User FK)

Communication
├── SmsNotificationConfig
├── SmsLog
│   ├── Parent (FK)
│   ├── Student (FK)
│   └── Contract (FK)
├── ChatGroup
│   ├── Classroom (FK)
│   ├── Students (M2M)
│   └── Members (User M2M)
└── ChatMessage
    ├── ChatGroup (FK)
    └── Sender (User FK)
```

## 3. INTEGRATSIYA NUQTALARI

### Call Centre → School ERP
```python
# Lead dan Student yaratish
Lead → StudentApplication → Student
     ↓                        ↓
  Parent                   Parent (M2M)
```

### API Endpoints
```
POST /students/api/add-student/
- Lead ma'lumotlaridan o'quvchi yaratish
- Ota-ona ma'lumotlarini ko'chirish
- Lead statusini "registered" ga o'zgartirish

POST /students/api/send-sms/
- SMS yuborish
- SMS logini saqlash
```

## 4. FOYDALANUVCHI ROLLARI

```
┌─────────────────────────────────────────────────────────────┐
│                        SUPERUSER                             │
│                    (Barcha huquqlar)                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────▼──────────┐                    ┌──────────▼─────────┐
│ ENROLLMENT       │                    │ STUDENTS           │
│ (Call Centre)    │                    │ (School ERP)       │
├──────────────────┤                    ├────────────────────┤
│ • enrollment_    │                    │ • students_        │
│   manager        │                    │   manager          │
│ • enrollment_    │                    │ • students_        │
│   agent          │                    │   agent            │
└──────────────────┘                    └────────────────────┘
```

## 5. TEXNOLOGIYALAR

### Backend
- **Framework**: Django 4.0+
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **ORM**: Django ORM
- **Authentication**: Django Auth + Groups

### Frontend
- **Template Engine**: Django Templates
- **CSS Framework**: Bootstrap 5 / Tailwind CSS
- **JavaScript**: Vanilla JS / jQuery
- **Icons**: Font Awesome / Bootstrap Icons

### Integratsiyalar
- **Twilio**: Qo'ng'iroqlar va yozib olish
- **Meta (Facebook/Instagram)**: Lead generation
- **SMS Gateway**: Eskiz.uz / Playmobile (kelajakda)
- **Redis**: Chat va real-time (ixtiyoriy)
- **Celery**: Asinxron vazifalar (ixtiyoriy)

### File Storage
- **Media Files**: Local storage / AWS S3
- **Static Files**: WhiteNoise
- **Call Recordings**: Twilio URL / Local / S3

## 6. XAVFSIZLIK

### Authentication
```python
@login_required
@students_required  # students_agent yoki students_manager
def view_function(request):
    pass
```

### Permissions
- Guruh asosida ruxsatlar
- View-level dekoratorlar
- Model-level permissions (Django admin)

### Data Protection
- CSRF protection
- SQL injection protection (ORM)
- XSS protection (template escaping)
- File upload validation
- Phone number masking (logs)

## 7. DEPLOYMENT ARXITEKTURASI

```
┌─────────────────────────────────────────────────────────────┐
│                      PRODUCTION                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Nginx      │─────▶│   Gunicorn   │                    │
│  │  (Reverse    │      │   (WSGI)     │                    │
│  │   Proxy)     │      └──────┬───────┘                    │
│  └──────────────┘             │                             │
│                               │                             │
│                    ┌──────────▼──────────┐                 │
│                    │   Django App        │                 │
│                    │   (Bakery + School) │                 │
│                    └──────────┬──────────┘                 │
│                               │                             │
│         ┌─────────────────────┼─────────────────────┐      │
│         │                     │                     │      │
│  ┌──────▼──────┐    ┌────────▼────────┐   ┌───────▼────┐ │
│  │ PostgreSQL  │    │  Redis (Cache)  │   │  AWS S3    │ │
│  │  Database   │    │  (Sessions)     │   │  (Media)   │ │
│  └─────────────┘    └─────────────────┘   └────────────┘ │
│                                                            │
│  ┌──────────────┐    ┌─────────────────┐                 │
│  │   Celery     │    │  Celery Beat    │                 │
│  │   Worker     │    │  (Scheduler)    │                 │
│  └──────────────┘    └─────────────────┘                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
         │                      │                    │
         │                      │                    │
    ┌────▼────┐          ┌──────▼──────┐     ┌──────▼──────┐
    │ Twilio  │          │    Meta     │     │ SMS Gateway │
    │   API   │          │  Webhook    │     │  (Eskiz.uz) │
    └─────────┘          └─────────────┘     └─────────────┘
```

## 8. URL STRUKTURA

```
/                           → Dashboard (core)
/admin/                     → Django Admin
/login/                     → Login page
/logout/                    → Logout

# Call Centre (Enrollment)
/enrollment/
├── /leads/                 → Lead list
├── /leads/new/             → Create lead
├── /leads/<id>/            → Lead detail
├── /applications/          → Application list
├── /call-centre/           → Call centre dashboard
├── /twilio/voice/          → Twilio voice webhook
├── /twilio/recording-status/ → Recording status webhook
└── /webhook/meta-lead/     → Meta lead webhook

# School ERP (Students)
/students/
├── /                       → Students dashboard
├── /list/                  → Students list
├── /new/                   → Create student
├── /<id>/                  → Student detail
├── /<id>/edit/             → Edit student
├── /classrooms/            → Classroom list
├── /classrooms/new/        → Create classroom
├── /classrooms/<id>/       → Classroom detail
├── /subjects/              → Subject list
├── /schedule/              → Schedule list
├── /schedule/new/          → Create schedule
├── /grades/daily/          → Daily grades
├── /grades/quarter/        → Quarter grades
├── /grades/results/        → Grade results
├── /attendance/            → Mark attendance
├── /homework/              → Homework list
├── /homework/new/          → Create homework
├── /<id>/finance/          → Student finance
├── /<id>/payment/add/      → Add payment
├── /<id>/contract/add/     → Add contract
├── /sms/config/            → SMS config
├── /sms/send-now/          → Send SMS now
├── /sms/logs/              → SMS logs
├── /chat/                  → Chat list
├── /chat/new/              → Create chat
├── /chat/<id>/             → Chat detail
└── /api/add-student/       → API: Create student
```

## 9. KELAJAKDAGI RIVOJLANISH

### Faza 1 (Joriy)
- ✅ Asosiy CRUD operatsiyalar
- ✅ Call Centre integratsiyasi
- ✅ SMS xabarnomalar (test mode)
- ✅ Ichki chat
- ✅ Moliya boshqaruvi

### Faza 2 (Keyingi 1-2 oy)
- [ ] Real SMS gateway integratsiyasi
- [ ] PDF hujjatlar generatsiyasi
- [ ] Excel export/import
- [ ] Email xabarnomalar
- [ ] Statistika va grafiklar

### Faza 3 (3-6 oy)
- [ ] Mobil ilova API
- [ ] Ota-onalar portali
- [ ] Online to'lovlar (Payme, Click)
- [ ] Biometrik davomat
- [ ] Video darslar integratsiyasi

### Faza 4 (6-12 oy)
- [ ] AI-powered analytics
- [ ] Avtomatik hisobotlar
- [ ] Multi-tenant arxitektura
- [ ] Mikroservislar
- [ ] Kubernetes deployment

## 10. MONITORING VA LOGGING

```python
# Logging konfiguratsiyasi
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/students.log',
        },
    },
    'loggers': {
        'students': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

### Monitoring Tools
- **Application**: Django Debug Toolbar (dev)
- **Database**: pgAdmin / DBeaver
- **Logs**: Papertrail / CloudWatch
- **Performance**: New Relic / DataDog
- **Errors**: Sentry

## 11. BACKUP STRATEGIYASI

```bash
# Database backup (kunlik)
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Media files backup (haftalik)
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# PostgreSQL backup
pg_dump dbname > backup_$(date +%Y%m%d).sql
```

## 12. TESTING STRATEGIYASI

```python
# Unit tests
python manage.py test students

# Coverage
coverage run --source='students' manage.py test students
coverage report

# Integration tests
python manage.py test students.tests.integration

# Load testing
locust -f locustfile.py
```

---

**Texnik hujjatlar yakunlandi! 🚀**
