from django.contrib import admin
from .models import (
    Classroom, Student, Parent, DocumentType, StudentDocument, DocumentTemplate,
    Subject, Schedule, Quarter, DailyGrade, QuarterGrade,
    Attendance, Homework, HomeworkSubmission,
    StudentBalance, MonthlyPayment, Contract, Payment,
    SmsNotificationConfig, SmsLog,
    ChatGroup, ChatMessage, ChatMessageRead, StudentTransfer
)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade', 'academic_year', 'homeroom_teacher', 'capacity']
    list_filter = ['academic_year', 'grade']
    search_fields = ['name']


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'phone', 'relation']
    search_fields = ['first_name', 'last_name', 'phone']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'classroom', 'gender', 'birth_date', 'is_active']
    list_filter = ['is_active', 'gender', 'classroom']
    search_fields = ['first_name', 'last_name', 'passport_or_id', 'erp_number']
    filter_horizontal = ['parents']


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_required']


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'doc_type', 'title', 'uploaded_by', 'uploaded_at']
    list_filter = ['doc_type', 'uploaded_at']
    search_fields = ['student__first_name', 'student__last_name', 'title']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['classroom', 'subject', 'day_of_week', 'start_time', 'end_time', 'teacher']
    list_filter = ['day_of_week', 'classroom']


@admin.register(Quarter)
class QuarterAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'number', 'start_date', 'end_date']
    list_filter = ['academic_year']


@admin.register(DailyGrade)
class DailyGradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'date', 'grade', 'teacher']
    list_filter = ['date', 'subject']
    search_fields = ['student__first_name', 'student__last_name']


@admin.register(QuarterGrade)
class QuarterGradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'quarter', 'grade', 'teacher']
    list_filter = ['quarter', 'subject']
    search_fields = ['student__first_name', 'student__last_name']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'subject', 'marked_by']
    list_filter = ['status', 'date']
    search_fields = ['student__first_name', 'student__last_name']


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ['classroom', 'subject', 'title', 'due_date', 'teacher']
    list_filter = ['due_date', 'classroom', 'subject']
    search_fields = ['title', 'description']
    filter_horizontal = ['students']


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ['homework', 'student', 'status', 'submitted_at', 'grade']
    list_filter = ['status', 'submitted_at']
    search_fields = ['homework__title', 'student__first_name', 'student__last_name']


@admin.register(StudentBalance)
class StudentBalanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'total_debt', 'last_updated']
    search_fields = ['student__first_name', 'student__last_name']
    readonly_fields = ['last_updated']


@admin.register(MonthlyPayment)
class MonthlyPaymentAdmin(admin.ModelAdmin):
    list_display = ['contract', 'month', 'amount_due', 'amount_paid', 'due_date', 'status']
    list_filter = ['status', 'month']
    search_fields = ['contract__student__first_name', 'contract__student__last_name']


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']


@admin.register(ChatMessageRead)
class ChatMessageReadAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username', 'message__text']


@admin.register(StudentTransfer)
class StudentTransferAdmin(admin.ModelAdmin):
    list_display = ['student', 'transfer_type', 'from_classroom', 'to_classroom', 'transfer_date']
    list_filter = ['transfer_type', 'transfer_date']
    search_fields = ['student__first_name', 'student__last_name']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['contract_number', 'student', 'monthly_fee', 'discount_percent', 'is_active', 'start_date']
    list_filter = ['is_active', 'start_date']
    search_fields = ['contract_number', 'student__first_name', 'student__last_name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'method', 'payment_date', 'month_for', 'received_by']
    list_filter = ['method', 'payment_date']
    search_fields = ['student__first_name', 'student__last_name']


@admin.register(SmsNotificationConfig)
class SmsNotificationConfigAdmin(admin.ModelAdmin):
    list_display = ['day_of_month', 'is_active']


@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = ['parent', 'student', 'phone', 'debt_amount', 'sent_at', 'is_sent']
    list_filter = ['is_sent', 'sent_at']
    search_fields = ['parent__first_name', 'parent__last_name', 'phone']


@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'classroom', 'created_by', 'created_at']
    filter_horizontal = ['students', 'members']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['group', 'sender', 'sent_at', 'is_read_by_admin']
    list_filter = ['sent_at', 'is_read_by_admin']
    search_fields = ['text']
