from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone


# ── Online Payment Gateway ────────────────────────────────────────────

class PaymentGateway(models.Model):
    """To'lov tizimlari (Payme, Click, Uzum...)"""
    PROVIDER_CHOICES = [
        ('payme', 'Payme'),
        ('click', 'Click'),
        ('uzum', 'Uzum Bank'),
        ('apelsin', 'Apelsin'),
        ('humo', 'Humo'),
        ('uzcard', 'UzCard'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, unique=True)
    merchant_id = models.CharField(max_length=100, blank=True, help_text='Tizim ichki merchant ID')
    api_key = models.CharField(max_length=500, blank=True)
    api_url = models.URLField(max_length=300, blank=True, help_text='API URL')
    is_active = models.BooleanField(default=True)
    is_test = models.BooleanField(default=False, help_text='Test rejimi')
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    callback_url = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['provider']

    def __str__(self):
        status = '(TEST)' if self.is_test else ''
        return f"{self.get_provider_display()} {status}"


class OnlinePayment(models.Model):
    """Online to'lov tizimlari orqali kelgan to'lovlar"""
    STATUS_CHOICES = [
        ('created', 'Yaratildi'),
        ('pending', 'Kutilmoqda'),
        ('paid', 'To\'landi'),
        ('failed', 'Xato'),
        ('cancelled', 'Bekor qilindi'),
        ('refunded', 'Qaytarildi'),
    ]

    provider = models.ForeignKey(PaymentGateway, on_delete=models.PROTECT, related_name='payments')
    transaction_id = models.CharField(max_length=200, unique=True, db_index=True)
    order_id = models.CharField(max_length=100, blank=True, db_index=True, help_text='Tizim ichki order ID')
    
    # Student/Contract linkage
    student_id = models.IntegerField(null=True, blank=True)
    student_name = models.CharField(max_length=200, blank=True)
    contract_number = models.CharField(max_length=100, blank=True)
    
    # Amount
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payment period
    month_for = models.DateField(null=True, blank=True, help_text='Qaysi oy uchun')
    description = models.CharField(max_length=300, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    
    # Callback data
    raw_request = models.JSONField(null=True, blank=True)
    raw_response = models.JSONField(null=True, blank=True)
    
    # Integration
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='online_payment_record'
    )
    journal_entry = models.ForeignKey(
        'JournalEntry', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='online_payment'
    )

    # User info
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.CharField(max_length=300, blank=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Online To\'lov'
        verbose_name_plural = 'Online To\'lovlar'

    def __str__(self):
        return f"{self.provider} | {self.transaction_id} | {self.amount:,.0f} | {self.get_status_display()}"
    
    def mark_paid(self):
        """To'lov muvaffaqiyatli bo'lganda"""
        self.status = 'paid'
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'confirmed_at'])
        
        # Create Payment record in students app
        self._create_student_payment()
        
        # Create GL journal entry
        self._create_gl_entry()
    
    def _create_student_payment(self):
        """Student payments jadvaliga yozish"""
        try:
            from students.models import Payment as StudentPayment
            # Import contract
            from students.models import Contract
            contract = None
            if self.contract_number:
                contract = Contract.objects.filter(contract_number=self.contract_number).first()
            
            student_id = self.student_id
            if student_id and not self.payment:
                student_payment = StudentPayment.objects.create(
                    student_id=student_id,
                    contract=contract,
                    amount=self.amount,
                    method=self.provider.provider,  # payme, click, etc.
                    payment_date=timezone.now().date(),
                    month_for=self.month_for or timezone.now().date(),
                    received_by=self.created_by,
                    note=f"Online to'lov: {self.transaction_id} ({self.provider})",
                    transaction_id=self.transaction_id,
                    is_confirmed=True,
                )
                self.payment = student_payment
                self.save(update_fields=['payment'])
        except ImportError:
            pass
    
    def _create_gl_entry(self):
        """GL jurnal yozuvini yaratish"""
        try:
            cash_reg = CashRegister.objects.filter(
                name__icontains='online'
            ).first() or CashRegister.objects.first()
            
            if not cash_reg:
                return
            
            memo = f"Online to'lov: {self.student_name} | {self.provider} | {self.transaction_id}"
            
            entry = JournalEntry.objects.create(
                memo=memo,
                status='posted',
                source='system',
                created_by=self.created_by,
            )
            
            # Debit: Cash/Bank
            revenue_acct = Account.objects.filter(
                code__startswith='1'
            ).first() or Account.objects.filter(
                name__icontains='kassa'
            ).first()
            
            if revenue_acct:
                JournalLine.objects.create(
                    entry=entry,
                    account=revenue_acct,
                    debit=self.amount,
                    description=f"{self.provider.get_provider_display()} tushum",
                )
            
            # Credit: Tuition revenue
            revenue_acct2 = Account.objects.filter(
                account_type='revenue'
            ).first()
            if revenue_acct2:
                JournalLine.objects.create(
                    entry=entry,
                    account=revenue_acct2,
                    credit=self.amount,
                    description=f"O'quvchi to'lovi: {self.student_name}",
                )
            
            self.journal_entry = entry
            self.save(update_fields=['journal_entry'])
        except Exception:
            pass


class Account(models.Model):
    """Hisoblar rejasi — Chart of Accounts."""

    ACCOUNT_TYPES = [
        ('asset', 'Aktiv'),
        ('liability', 'Majburiyat'),
        ('equity', 'Kapital'),
        ('revenue', 'Daromad'),
        ('expense', 'Xarajat'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"


class CashRegister(models.Model):
    name = models.CharField(max_length=255, help_text="e.g., Main, Terminal, Expense")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    gl_account = models.OneToOneField(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cash_register',
    )

    def __str__(self):
        return f"{self.name} — {self.balance}"


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=255, help_text="e.g., Utilities, Raw Materials, Household")

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_info = models.TextField(blank=True, null=True)
    debt = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} (Qarz: {self.debt})"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
        ('supplier_payment', 'Supplier Payment'),
    ]
    date = models.DateTimeField(auto_now_add=True)
    cash_register = models.ForeignKey(CashRegister, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True, null=True)

    expense_category = models.ForeignKey(
        ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True
    )
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    transfer_to = models.ForeignKey(
        CashRegister, on_delete=models.SET_NULL, related_name='incoming_transfers', null=True, blank=True
    )

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.amount} @ {self.date:%Y-%m-%d}"


class JournalEntry(models.Model):
    """Jurnal sarlavhasi — ikki tomonlama yozuvlar to‘plami."""

    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('posted', 'Tasdiqlangan'),
    ]
    SOURCE_CHOICES = [
        ('manual', 'Qo‘lda jurnal'),
        ('cash', 'Kassa operatsiyasi'),
        ('sales', 'POS savdo'),
        ('branch', 'Filial savdo'),
        ('system', 'Tizim'),
    ]

    entry_date = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=64, blank=True)
    memo = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='posted')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='journal_entry',
    )

    class Meta:
        ordering = ['-entry_date', '-id']

    def __str__(self):
        return f"JE #{self.id} {self.entry_date:%Y-%m-%d} {self.reference or ''}"

    def total_debit(self):
        return self.lines.aggregate(t=Sum('debit'))['t'] or 0

    def total_credit(self):
        return self.lines.aggregate(t=Sum('credit'))['t'] or 0


class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='journal_lines')
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.account.code} D{self.debit} C{self.credit}"

    def clean(self):
        super().clean()
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("Bir qatorda faqat debet yoki faqat kredit bo‘lishi kerak.")
        if self.debit < 0 or self.credit < 0:
            raise ValidationError("Manfiy summalar ruxsat etilmaydi.")
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("Debet yoki kiritdan biri musbat bo‘lishi kerak.")
