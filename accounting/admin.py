from django.contrib import admin

from .models import (
    Account, CashRegister, ExpenseCategory, JournalEntry, JournalLine,
    Supplier, Transaction, PaymentGateway
)


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 0


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'is_active')
    list_filter = ('account_type', 'is_active')
    search_fields = ('code', 'name')


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ('name', 'balance', 'gl_account')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'entry_date', 'reference', 'source', 'status', 'created_by')
    list_filter = ('source', 'status')
    inlines = [JournalLineInline]
    search_fields = ('reference', 'memo')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'transaction_type', 'amount', 'cash_register')
    list_filter = ('transaction_type',)


admin.site.register(ExpenseCategory)
admin.site.register(Supplier)


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ('provider', 'merchant_id', 'is_active', 'is_test', 'commission_percent')
    list_filter = ('is_active', 'is_test', 'provider')
    list_editable = ('is_active', 'is_test')
    search_fields = ('provider', 'merchant_id')
