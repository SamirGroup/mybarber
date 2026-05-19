from django.contrib import admin
from django.utils.html import format_html
from .models import MetaLead, LeadStatus, LeadStatusHistory, LeadComment, Callback, Notification, ApiLog, SystemSettings


@admin.register(LeadStatus)
class LeadStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'color', 'sort_order')
    list_editable = ('code', 'color', 'sort_order')
    search_fields = ('name', 'code')


@admin.register(MetaLead)
class MetaLeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone_number', 'current_status', 'assigned_operator', 'campaign_name', 'crm_received_time', 'created_actions')
    list_filter = ('current_status', 'is_closed', 'assigned_operator', 'region', 'campaign_name')
    search_fields = ('full_name', 'phone_number', 'lead_uuid')
    raw_id_fields = ('assigned_operator', 'current_status')
    date_hierarchy = 'crm_received_time'
    readonly_fields = ('lead_uuid', 'raw_payload', 'crm_received_time')

    fieldsets = (
        ('Lead ma\'lumotlari', {
            'fields': ('lead_uuid', 'full_name', 'phone_number', 'phone_number2', 'region', 'product_interest')
        }),
        ('Meta/Ads', {
            'fields': ('campaign_name', 'adset_name', 'form_name', 'meta_created_time')
        }),
        ('Holat & biriktirish', {
            'fields': ('assigned_operator', 'current_status', 'is_closed', 'callback_date')
        }),
        ('Texnik', {
            'fields': ('raw_payload', 'crm_received_time'),
            'classes': ('collapse',)
        }),
    )

    def created_actions(self, obj):
        return format_html('<small>{}</small>', obj.crm_received_time.strftime('%d.%m %H:%M'))
    created_actions.short_description = 'Qabul vaqti'


@admin.register(LeadStatusHistory)
class LeadStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('lead', 'old_status', 'new_status', 'operator', 'changed_at')
    list_filter = ('new_status', 'changed_at')
    search_fields = ('lead__full_name',)
    raw_id_fields = ('lead', 'old_status', 'new_status', 'operator')


@admin.register(LeadComment)
class LeadCommentAdmin(admin.ModelAdmin):
    list_display = ('lead', 'operator', 'comment_preview', 'created_at')
    list_filter = ('created_at', 'operator')
    search_fields = ('lead__full_name', 'comment_text')

    def comment_preview(self, obj):
        return obj.comment_text[:80] + '...' if len(obj.comment_text) > 80 else obj.comment_text
    comment_preview.short_description = 'Izoh'


@admin.register(Callback)
class CallbackAdmin(admin.ModelAdmin):
    list_display = ('lead', 'callback_datetime', 'created_by', 'is_done', 'created_at')
    list_filter = ('is_done', 'callback_datetime')
    search_fields = ('lead__full_name',)
    raw_id_fields = ('lead', 'created_by')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'lead', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'lead__full_name', 'notification_text')
    raw_id_fields = ('user', 'lead')


@admin.register(ApiLog)
class ApiLogAdmin(admin.ModelAdmin):
    list_display = ('api_name', 'status_code', 'created_at')
    list_filter = ('api_name', 'status_code', 'created_at')
    readonly_fields = ('api_name', 'request_payload', 'response_payload', 'status_code', 'created_at')


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'assign_mode', 'round_robin_index', 'meta_access_token_preview')
    fieldsets = (
        ('Lead taqsimot', {
            'fields': ('assign_mode', 'round_robin_index')
        }),
        ('Meta API', {
            'fields': ('meta_verify_token', 'meta_access_token', 'meta_app_secret', 'meta_page_id')
        }),
    )

    def meta_access_token_preview(self, obj):
        if obj.meta_access_token:
            return obj.meta_access_token[:10] + '...'
        return '—'
    meta_access_token_preview.short_description = 'Token'
