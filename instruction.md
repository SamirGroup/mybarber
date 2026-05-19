# Online To'lov Integratsiyasi - To'liq Qo'llanma

O'quvchilar shartnomasi bo'yicha onlayn to'lovlarni Payme, Click, Uzum Bank va boshqa o'zbekistonlik to'lov tizimlari bilan integratsiya qilish bo'yicha to'liq ko'rsatma.

---

## 📋 Mazmun

1. [Loyiha Tuzilishi](#1-loyiha-tuzilishi)
2. [Kerakli API'lar va Ro'yxatdan O'tish](#2-kerakli-api-lar-va-royxatdan-o-tish)
3. [API So'rovlarini Olish Ketma-ketligi](#3-api-so-rovlarini-olish-ketma-ketligi)
4. [Kodga Integratsiya Qilish](#4-kodga-integratsiya-qilish)
5. [Test Muhitini Sozlash](#5-test-muhitini-sozlash)
6. [Prod Muhitga Chiqarish](#6-prod-muhitga-chiqarish)
7. [Xavfsizlik Va Tekshiruv](#7-xavfsizlik-va-tekshiruv)

---

## 1. Loyiha Tuzilishi

```
bakery_erp/
├── students/
│   ├── models.py              # PaymentGateway, OnlinePayment modellari
│   ├── gateway_api.py         # Barcha to'lov provayderlari API klasslari
│   ├── views.py               # Webhook handlers va payment start/init
│   ├── urls.py                # Payment va webhook route'lar
│   └── templates/students/
│       └── payment_init.html  # To'lov tanlash sahifasi
├── accounting/
│   ├── models.py              # JournalEntry, Payment modellari
│   ├── services.py            # GL jurnal yozuvlari uchun funksiyalar
│   └── views.py               # Buxgalteriya ko'rinishlari
└── instruction.md             # Ushbu fayl
```

### Asosiy Fayllar

| Fayl | Vazifasi |
|------|----------|
| `students/models.py` | PaymentGateway (API credentials), OnlinePayment (transaction records) |
| `students/gateway_api.py` | Har bir to'lov provayderi uchun API integration klasslar |
| `students/views.py` | Webhook handlers, payment init/start logikasi |
| `students/urls.py` | `/payment/init/`, `/payment/start/`, `/webhook/*` route'lar |
| `accounting/services.py` | Buxgalteriya GL jurnal yozuvlarini yaratish |

---

## 2. Kerakli API'lar va Ro'yxatdan O'tish

### 2.1. Qaysi Tizimlardan API Olish Kerak?

O'zbekistonda eng keng tarqalgan to'lov tizimlari:

#### A. Asosiy Tizimlar (Majburiy)

| Tizim | Veb-sayt | API Hujjatlari | Qiyinchilik |
|-------|----------|----------------|-------------|
| **Payme** | https://payme.uz | https://developer.payme.uz | O'rta |
| **Click** | https://click.uz | https://merchant.click.uz | O'rta |
| **Uzum Bank** | https://bank.uzum.uz | https://developer.uzum.uz | Oson |
| **Apelsin** | https://apelsin.uz | https://merchant.apelsin.uz | O'rta |

#### B. Qo'shimcha Tizimlar (Tavsiya etiladi)

| Tizim | Veb-sayt | API Hujjatlari | Qiyinchilik |
|-------|----------|----------------|-------------|
| **CAP (KAP)** | https://cap.uz | https://merchant.cap.uz | O'rta |
| **Humo** | https://humo.uz | https://developer.humo.uz | Oson |
| **UzCard** | https://uzcard.uz | https://merchant.uzcard.uz | O'rta |
| **Payme Business** | https://payme.uz/business | https://developer.payme.uz/business | O'rta |

---

### 2.2. Har Bir Tizimdan API Olish Ketma-ketligi

#### 🔹 PAYME

1. **Ro'yxatdan o'tish:**
   - https://merchant.payme.uz saytiga kiring
   - "Ro'yxatdan o'tish" tugmasini bosing
   - Tashkilot ma'lumotlarini kiriting (INN, manzil, telefon)

2. **Merchant Account yaratish:**
   - Shaxsiy kabinetga kirganingizdan keyin
   - "Merchant" bo'limida yangi merchant yarating
   - Tashkilot hujjatlarini yuklang (O'zbekiston Respublikasi qonunlariga muvofiq)

3. **API So'rovlarini olish:**
   ```
   - merchant_id (Merchant ID)
   - api_key (API Kalit)
   - secret_key (Maxfiy kalit)
   ```

4. **Webhook URL sozlash:**
   ```
   https://sizning-saytingiz.uz/students/webhook/payme/
   ```

5. **Test muhitini tekshirish:**
   - Payme test modda: `https://test.payme.uz`
   - Test kartalar orqali sinov to'lovlar

---

#### 🔹 CLICK

1. **Ro'yxatdan o'tish:**
   - https://merchant.click.uz saytiga kiring
   - "Partner ro'yxatdan o'tish" tugmasini bosing

2. **Partner yaratish:**
   - Tashkilot ma'lumotlarini to'ldiring
   - INN orqali avtomatik tekshiruv
   - Bank hisobvaraqlari ma'lumotlari

3. **API So'rovlarini olish:**
   ```
   - service_id (Xizmat ID)
   - service_key (Xizmat kaliti)
   - public_key (Ommaviy kalit)
   ```

4. **Webhook URL sozlash:**
   ```
   https://sizning-saytingiz.uz/students/webhook/click/
   ```

5. **Test muhiti:**
   - Test server: `https://test-api.click.uz`
   - Test kartalar: merchant panelda mavjud

---

#### 🔹 UZUM BANK

1. **Ro'yxatdan o'tish:**
   - https://bank.uzum.uz/merchant saytiga kiring
   - "Integratsiya" bo'limiga o'ting

2. **Merchant yarating:**
   - Tashkilot ma'lumotlari
   - Bank hisobvaraqi raqami
   - Kontakt shaxs ma'lumotlari

3. **API So'rovlarini olish:**
   ```
   - merchant_id
   - api_key
   - webhook_secret
   ```

4. **Webhook URL sozlash:**
   ```
   https://sizning-saytingiz.uz/students/webhook/uzum/
   ```

5. **Test muhiti:**
   - Sandbox: `https://sandbox-api.uzum.uz`
   - Test API key sandbox panelda mavjud

---

#### 🔹 APELSIN

1. **Ro'yxatdan o'tish:**
   - https://merchant.apelsin.uz saytiga kiring
   - "Partner bo'lish" tugmasini bosing

2. **Ariza topshirish:**
   - Tashkilot haqida to'liq ma'lumot
   - INN va boshqa hujjatlar
   - Kontakt telefon va email

3. **API So'rovlarini olish:**
   ```
   - merchant_id
   - api_key
   - secret_key
   ```

4. **Webhook URL sozlash:**
   ```
   https://sizning-saytingiz.uz/students/webhook/apelsin/
   ```

---

#### 🔹 CAP (KAP)

1. **Ro'yxatdan o'tish:**
   - https://merchant.cap.uz saytiga kiring

2. **Partner ro'yxatdan o'tish:**
   - Tashkilot ma'lumotlari
   - Bank ma'lumotlari

3. **API So'rovlarini olish:**
   ```
   - merchant_code
   - api_key
   - secret_key
   ```

4. **Webhook URL sozlash:**
   ```
   https://sizning-saytingiz.uz/students/webhook/cap/
   ```

---

#### 🔹 HUMO / UZCARD

1. **Ro'yxatdan o'tish:**
   - Humo: https://developer.humo.uz
   - UzCard: https://merchant.uzcard.uz

2. **Integratsiya arizasini topshirish:**
   - Tashkilot hujjatlari
   - Bank kelishuvi

3. **API So'rovlarini olish:**
   ```
   - terminal_id
   - merchant_key
   - secret_key
   ```

4. **Webhook URL sozlash:**
   ```
   https://sizning-saytingiz.uz/students/webhook/humo/
   ```

---

## 3. API So'rovlarini Olish Ketma-ketligi

### Bosqichma-bosqich Jarayon

```
1. Tashkilot hujjatlarini tayyorlash
   ├── O'zbekiston Respublikasi qonunlariga muvofiq ro'yxatdan o'tgan
   ├── INN (Identifikatsiya raqami)
   ├── Bank hisobvaraqlari
   └── Kontakt ma'lumotlar

2. Har bir to'lov tizimiga alohida ariza topshirish
   ├── Payme → 2-3 kun
   ├── Click → 2-3 kun
   ├── Uzum → 1-2 kun
   ├── Apelsin → 2-3 kun
   └── CAP/Humo/UzCard → 3-5 kun

3. Har bir tizimdan API kalitlarni olish
   ├── merchant_id / service_id
   ├── api_key / secret_key
   └── public_key (agar kerak bo'lsa)

4. Test muhitida sinovlar
   ├── Test kartalar bilan to'lov
   ├── Webhook qabul qilishni tekshirish
   └── Buxgalteriya integratsiyasini test

5. Prod muhitga o'tish
   ├── Haqiqiy kartalar bilan sinov
   ├── Barcha holatlarni test qilish
   └── Monitoring va logging
```

---

## 4. Kodga Integratsiya Qilish

### 4.1. Model Sozlamalari

`students/models.py` faylida `PaymentGateway` modeli allaqachon mavjud:

```python
class PaymentGateway(models.Model):
    PROVIDER_CHOICES = [
        ('payme', 'Payme'),
        ('click', 'Click'),
        ('uzum', 'Uzum Bank'),
        ('apls', 'Apelsin'),
        ('cap', 'CAP'),
        ('humo', 'Humo'),
        ('uzcard', 'UzCard'),
        ('payme_business', 'Payme Business'),
    ]
    
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    merchant_id = models.CharField(max_length=100)
    api_key = models.CharField(max_length=200)
    secret_key = models.CharField(max_length=200)
    test_mode = models.BooleanField(default=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
```

**Qilishingiz kerak:**
1. Admin panelda har bir provider uchun credentials kiriting
2. `test_mode = True` bo'lsin (avval test muhitida ishlash uchun)
3. Commission rate'ni to'g'ri kiriting (har bir provider o'z foizini oladi)

---

### 4.2. Gateway API Klasslari

`students/gateway_api.py` faylida har bir provider uchun alohida klass:

```python
class PaymeGateway:
    """Payme API integratsiyasi"""
    def __init__(self, merchant_id, api_key, test_mode=False):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.base_url = 'https://test.payme.uz' if test_mode else 'https://payme.uz'
    
    def create_payment(self, amount, order_id, customer_info):
        # Payme API chaqiruvi
        pass
    
    def verify_payment(self, transaction_id):
        # To'lovni tekshirish
        pass
    
    def verify_webhook_signature(self, payload, signature):
        # Webhook imzosini tekshirish
        pass

class ClickGateway:
    """Click API integratsiyasi"""
    def __init__(self, service_id, service_key, test_mode=False):
        self.service_id = service_id
        self.service_key = service_key
        self.base_url = 'https://test-api.click.uz' if test_mode else 'https://api.click.uz'
    
    def create_payment(self, amount, order_id, customer_info):
        pass
    
    def verify_payment(self, transaction_id):
        pass

# Boshqa provider klasslar...
```

---

### 4.3. Views - Webhook Handlers

`students/views.py` faylida webhook handlerlar:

```python
@csrf_exempt
def payme_webhook(request):
    """Payme webhook handler"""
    if request.method == 'POST':
        payload = json.loads(request.body)
        signature = request.headers.get('X-Signature')
        
        # Imzo tekshirish
        gateway = PaymeGateway(...)
        if not gateway.verify_webhook_signature(payload, signature):
            return JsonResponse({'error': 'Invalid signature'}, status=403)
        
        # To'lov ma'lumotlarini olish
        transaction_id = payload.get('transaction_id')
        amount = payload.get('amount')
        order_id = payload.get('order_id')
        
        # OnlinePayment recordini yangilash
        online_payment = OnlinePayment.objects.get(transaction_id=transaction_id)
        online_payment.status = 'paid'
        online_payment.provider_transaction_id = transaction_id
        online_payment.save()
        
        # Buxgalteriya yozuvi yaratish
        _confirm_online_payment(online_payment)
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Boshqa webhook handlers...
```

---

### 4.4. Buxgalteriya Integratsiyasi

Har bir to'lov tasdiqlanganda buxgalteriyada jurnal yozuvi yaratiladi:

```python
def _confirm_online_payment(online_payment):
    """Buxgalteriyada to'lovni tasdiqlash"""
    
    # 1. Payment record yaratish
    payment = Payment.objects.create(
        student=online_payment.student,
        contract=online_payment.contract,
        amount=online_payment.amount,
        payment_date=timezone.now(),
        method='online',
        is_confirmed=True,
        transaction_id=online_payment.transaction_id
    )
    
    # 2. JournalEntry yaratish (GL)
    journal_entry = JournalEntry.objects.create(
        description=f"Online payment - {online_payment.provider} - {online_payment.transaction_id}",
        entry_date=timezone.now(),
        reference_type='online_payment',
        reference_id=online_payment.id
    )
    
    # 3. GL Lines yaratish
    # Debit: Cash account (pul keldi)
    JournalLine.objects.create(
        journal_entry=journal_entry,
        account=cash_account,  # Naqd/Pul hisobvaraqi
        debit=online_payment.amount,
        credit=0
    )
    
    # Credit: Revenue account (daromad)
    JournalLine.objects.create(
        journal_entry=journal_entry,
        account=revenue_account,  # Daromad hisobvaraqi
        debit=0,
        credit=online_payment.amount
    )
```

---

### 4.5. URL Route'lar

`students/urls.py` faylida route'lar allaqachon qo'shilgan:

```python
# To'lov boshlash
path('<int:pk>/payment/init/', views.payment_init, name='students_payment_init'),
path('<int:pk>/payment/start/', views.payment_start, name='students_payment_start'),

# Webhook endpoints
path('webhook/payme/', views.payme_webhook, name='students_payme_webhook'),
path('webhook/click/', views.click_webhook, name='students_click_webhook'),
path('webhook/uzum/', views.uzum_webhook, name='students_uzum_webhook'),
path('webhook/apelsin/', views.apls_webhook, name='students_apls_webhook'),
path('webhook/cap/', views.cap_webhook, name='students_cap_webhook'),
path('webhook/humo/', views.uzum_webhook, name='students_humo_webhook'),
```

---

## 5. Test Muhitini Sozlash

### 5.1. Test Provider Sozlamalari

Admin panelda har bir provider uchun test credentials kiriting:

```
PaymentGateway yaratish:
├── Provider: Payme
├── Merchant ID: test_merchant_id
├── API Key: test_api_key
├── Secret Key: test_secret_key
├── Test Mode: ☑ True
└── Commission Rate: 0 (testda foiz yo'q)
```

### 5.2. Test To'lovlar

1. **Payme test kartalar:**
   - Card: 9999 9999 9999 9999
   - Expiry: 12/25
   - CVV: 123

2. **Click test kartalar:**
   - Merchant panelda test kartalar ro'yxati mavjud

3. **Uzum sandbox:**
   - Test API key sandbox panelda

### 5.3. Ngrok Ishlatish (Local Testing)

Agar local muhitda ishlasangiz, webhook qabul qilish uchun ngrok kerak:

```bash
# Ngrok o'rnatish
pip install pyngrok

# Ngrok ishga tushirish
ngrok http 8000

# Natija: https://abc123.ngrok.io → http://localhost:8000
```

Webhook URL ni ngrok manziliga o'rnating:
```
https://abc123.ngrok.io/students/webhook/payme/
```

---

## 6. Prod Muhitga Chiqarish

### 6.1. Sozlamalarni O'zgartirish

1. **Test mode ni o'chirish:**
   ```python
   # Admin panelda har bir provider uchun
   test_mode = False
   ```

2. **Haqiqiy API kalitlarni kiriting:**
   ```
   Merchant ID (haqiqiy)
   API Key (haqiqiy)
   Secret Key (haqiqiy)
   ```

3. **Production URL'larni sozlash:**
   ```
   Webhook URL: https://sizning-saytingiz.uz/students/webhook/payme/
   ```

### 6.2. Xavfsizlik Tekshiruvi

```python
# Webhook imzosini DOIM tekshiring
if not gateway.verify_webhook_signature(payload, signature):
    return JsonResponse({'error': 'Invalid signature'}, status=403)

# Amount mosligini tekshiring
if online_payment.amount != payload.get('amount'):
    logger.error(f"Amount mismatch: {online_payment.amount} vs {payload.get('amount')}")
    return JsonResponse({'error': 'Amount mismatch'}, status=400)

# Idempotency (takroriy to'lovni oldini olish)
if online_payment.status == 'paid':
    return JsonResponse({'status': 'already_paid'})
```

### 6.3. Monitoring va Logging

```python
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def payme_webhook(request):
    try:
        logger.info(f"Payme webhook received: {request.body}")
        # ... processing ...
        logger.info(f"Payment confirmed: {online_payment.transaction_id}")
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Internal error'}, status=500)
```

---

## 7. Xavfsizlik Va Tekshiruv

### 7.1. Xavfsizlik Cheklovlari

✅ **Qilish kerak:**
- Webhook imzosini har doim tekshirish
- HTTPS ni majburiy qilib qo'yish
- Rate limiting qo'shish
- IP whitelisting (provider IP'larini)
- API kalitlarni environment variable'da saqlash

❌ **Qilmaslik kerak:**
- API kalitlarni kod ichida saqlamaslik
- Webhook imzosini tekshirmaslik
- HTTP orqali webhook qabul qilmaslik
- Test credentials ni prod ga qoldirmaslik

### 7.2. Environment Variables

`.env` fayl yaratish:

```env
# Payme
PAYME_MERCHANT_ID=your_merchant_id
PAYME_API_KEY=your_api_key
PAYME_SECRET_KEY=your_secret_key

# Click
CLICK_SERVICE_ID=your_service_id
CLICK_SERVICE_KEY=your_service_key

# Uzum
UZUM_MERCHANT_ID=your_merchant_id
UZUM_API_KEY=your_api_key

# Boshqa provider'lar...
```

`.env` ni `.gitignore` ga qo'shing:
```gitignore
.env
*.env
```

### 7.3. Tekshiruv Ro'yxati

Prod ga chiqishdan oldin:

```
☐ Barcha provider'lar test modda sinovdan o'tkazildi
☐ Webhook imzolari to'g'ri tekshiriladi
☐ Buxgalteriya integratsiyasi ishlayapti
☐ Amount mosligi tekshiriladi
☐ Idempotency qo'shilgan (takroriy to'lov yo'q)
☐ Logging va monitoring sozlangan
☐ Error handling to'liq
☐ HTTPS majburiy
☐ API kalitlar environment variable'da
☐ Test mode = False
☐ Haqiqiy API kalitlar kiritildi
☐ Commission rate'lar to'g'ri
☐ Mobile va desktop test qilindi
☐ To'lov muvaffaqiyatli holati
☐ To'lov rad etilgan holati
☐ To'lov qaytarish (refund) holati
```

---

## 8. Muammolarni Hal Qilish

### 8.1. Webhook Kelmayapti

**Sabablar:**
- Server darajasida firewall
- Provider webhook URL noto'g'ri
- Server response 200 qaytarmayapti

**Yechim:**
```bash
# Server loglarini tekshiring
tail -f /var/log/nginx/error.log

# Webhook URL ni provider panelda tekshiring
# Response code 200 bo'lishi kerak
```

### 8.2. To'lov Tasdiqlandi Lekin Buxgalteriyada Ko'rinmayapti

**Tekshirish:**
```python
# Admin panelda OnlinePayment recordini oching
# status = 'paid' bo'lishi kerak

# Payment record yaratilganmi?
Payment.objects.filter(transaction_id=online_payment.transaction_id)

# JournalEntry yaratilganmi?
JournalEntry.objects.filter(reference_id=online_payment.id)
```

### 8.3. Amount Noto'g'ri

**Sabab:** Provider foizni hisoblamayapti

**Yechim:**
```python
# Commission rate'ni to'g'ri kiriting
# Provider foizni hisoblagandan keyin netto amount qaytadi

# Yoki gross amount saqlang, commission alohida
gross_amount = online_payment.amount
commission = gross_amount * (gateway.commission_rate / 100)
net_amount = gross_amount - commission
```

---

## 9. Foydali Havolalar

### API Hujjatlari
- [Payme Developer](https://developer.payme.uz)
- [Click Merchant](https://merchant.click.uz)
- [Uzum Developer](https://developer.uzum.uz)
- [Apelsin Merchant](https://merchant.apelsin.uz)
- [CAP Merchant](https://merchant.cap.uz)
- [Humo Developer](https://developer.humo.uz)
- [UzCard Merchant](https://merchant.uzcard.uz)

### Qo'shimcha Resurslar
- [Django Documentation](https://docs.djangoproject.com/)
- [Webhook Best Practices](https://webhook.site)
- [Ngrok](https://ngrok.com)

---

## 10. Qo'shimcha Savollar

Agar savollaringiz bo'lsa:
- Provider support ga murojaat qiling
- Django forumlari
- O'zbekiston IT hamjamiatlari

---

**Yaratilgan:** 2024-yil
**Versiya:** 1.0
**So'nggi yangilanish:** 2024
