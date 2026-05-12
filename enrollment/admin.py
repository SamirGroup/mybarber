from django.contrib import admin
from .models import (
    LeadSource, Grade, AcademicYear, Lead,
    CallCampaign, CallRecord, StudentApplication, AgentProfile,
)


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'sort_order')
    ordering = ('sort_order',)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'status', 'source', 'assigned_to', 'created_at')
    list_filter = ('status', 'source', 'assigned_to', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'child_name', 'meta_lead_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CallCampaign)
class CallCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_by', 'created_at')


@admin.register(CallRecord)
class CallRecordAdmin(admin.ModelAdmin):
    list_display = ('caller_number', 'callee_number', 'direction', 'status', 'agent', 'lead', 'created_at')
    list_filter = ('direction', 'status', 'agent', 'created_at')
    search_fields = ('caller_number', 'callee_number', 'twilio_call_sid')
    readonly_fields = ('created_at',)


@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = ('student_first_name', 'student_last_name', 'applying_grade', 'status', 'parent_phone', 'created_at')
    list_filter = ('status', 'applying_grade', 'student_gender', 'created_at')
    search_fields = ('student_first_name', 'student_last_name', 'parent_phone', 'parent_first_name', 'parent_last_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'extension', 'is_available')
    list_filter = ('is_available',)

