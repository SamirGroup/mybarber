from django.contrib import admin
from .models import (
    LeadSource, Grade, AcademicYear, Lead,
    CallCampaign, CallRecord, StudentApplication, AgentProfile,
    LeadStatusHistory, LeadComment, CallQueue, CallRouting, AuditLog, CallStatistics,
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


class LeadStatusHistoryInline(admin.TabularInline):
    model = LeadStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'notes', 'created_at')
    can_delete = False


class LeadCommentInline(admin.TabularInline):
    model = LeadComment
    extra = 1
    readonly_fields = ('user', 'created_at')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'children_count', 'interested_grade', 'status', 'source', 'assigned_to', 'created_at')
    list_filter = ('status', 'source', 'assigned_to', 'created_at', 'interested_grade')
    search_fields = ('first_name', 'last_name', 'phone', 'phone_2', 'child_name', 'meta_lead_id', 'meta_campaign_name')
    readonly_fields = ('created_at', 'updated_at', 'meta_lead_id')
    inlines = [LeadCommentInline, LeadStatusHistoryInline]
    fieldsets = (
        ('Ota-ona ma\'lumotlari', {
            'fields': ('first_name', 'last_name', 'phone', 'phone_2', 'email', 'region')
        }),
        ('Qabul ma\'lumotlari', {
            'fields': ('interested_grade', 'children_count', 'child_name', 'child_age', 'discount_info')
        }),
        ('Meta ma\'lumotlari', {
            'fields': ('source', 'meta_lead_id', 'meta_campaign_name', 'meta_adset_name', 'meta_form_name',
                      'meta_campaign_id', 'meta_adset_id', 'meta_ad_id', 'meta_form_id'),
            'classes': ('collapse',)
        }),
        ('Status va tayinlash', {
            'fields': ('status', 'assigned_to', 'contacted_at', 'notes')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CallCampaign)
class CallCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_by', 'created_at')


@admin.register(CallRecord)
class CallRecordAdmin(admin.ModelAdmin):
    list_display = ('caller_number', 'callee_number', 'direction', 'status', 'agent', 'lead', 'duration_seconds', 'recording_consent', 'created_at')
    list_filter = ('direction', 'status', 'recording_consent', 'agent', 'created_at', 'is_flagged')
    search_fields = ('caller_number', 'callee_number', 'twilio_call_sid', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'formatted_duration')
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('lead', 'campaign', 'agent', 'caller_number', 'callee_number', 'direction', 'status')
        }),
        ('Twilio', {
            'fields': ('twilio_call_sid', 'twilio_conference_sid'),
            'classes': ('collapse',)
        }),
        ('Yozuv', {
            'fields': ('recording_consent', 'recording_consent_timestamp', 'recording_url', 'recording_sid', 'recording_file', 'recording_duration')
        }),
        ('Vaqt va metrikalar', {
            'fields': ('duration_seconds', 'wait_time_seconds', 'talk_time_seconds', 'formatted_duration', 'started_at', 'answered_at', 'ended_at')
        }),
        ('Sifat nazorati', {
            'fields': ('quality_score', 'reviewed_by', 'reviewed_at', 'is_flagged', 'disposition', 'tags', 'notes')
        }),
        ('Tizim', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_duration(self, obj):
        return obj.formatted_duration
    formatted_duration.short_description = 'Davomiylik'


@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = ('student_first_name', 'student_last_name', 'applying_grade', 'status', 'parent_phone', 'created_at')
    list_filter = ('status', 'applying_grade', 'student_gender', 'created_at')
    search_fields = ('student_first_name', 'student_last_name', 'parent_phone', 'parent_first_name', 'parent_last_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'extension', 'phone_number', 'status', 'is_available', 'total_calls_handled', 'last_call_at')
    list_filter = ('status', 'is_available')
    search_fields = ('user__username', 'extension', 'phone_number')
    readonly_fields = ('total_calls_handled', 'last_call_at', 'created_at', 'updated_at')


@admin.register(CallQueue)
class CallQueueAdmin(admin.ModelAdmin):
    list_display = ('call', 'queue_name', 'status', 'priority', 'position', 'wait_time_seconds', 'assigned_agent', 'entered_at')
    list_filter = ('status', 'queue_name', 'entered_at')
    search_fields = ('call__caller_number', 'assigned_agent__username')
    readonly_fields = ('entered_at', 'assigned_at', 'answered_at', 'left_at')


@admin.register(CallRouting)
class CallRoutingAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'strategy', 'is_active', 'max_queue_size', 'created_at')
    list_filter = ('is_active', 'strategy', 'business_hours_only')
    search_fields = ('name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'target_model', 'target_id', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at', 'user')
    search_fields = ('user__username', 'description', 'ip_address')
    readonly_fields = ('created_at',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CallStatistics)
class CallStatisticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'agent', 'total_calls', 'answered_calls', 'missed_calls', 'avg_duration_seconds', 'recordings_count')
    list_filter = ('date', 'agent')
    search_fields = ('agent__username',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'


@admin.register(LeadStatusHistory)
class LeadStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('lead', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('new_status', 'created_at')
    search_fields = ('lead__first_name', 'lead__last_name', 'lead__phone')
    readonly_fields = ('lead', 'old_status', 'new_status', 'changed_by', 'created_at')


@admin.register(LeadComment)
class LeadCommentAdmin(admin.ModelAdmin):
    list_display = ('lead', 'user', 'comment_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('lead__first_name', 'lead__last_name', 'comment')
    readonly_fields = ('created_at',)

    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Izoh'

