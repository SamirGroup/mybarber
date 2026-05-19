from django.contrib import admin
from .models import CameraConfig, FaceProfile, FaceCheckLog


@admin.register(CameraConfig)
class CameraConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'scope', 'device_label', 'is_default', 'is_active', 'updated_at')
    list_filter = ('scope', 'is_active', 'is_default')


@admin.register(FaceProfile)
class FaceProfileAdmin(admin.ModelAdmin):
    list_display = ('person_type', 'student', 'employee', 'is_active', 'enrolled_at')
    list_filter = ('person_type', 'is_active')


@admin.register(FaceCheckLog)
class FaceCheckLogAdmin(admin.ModelAdmin):
    list_display = ('checked_at', 'scope', 'result', 'student', 'employee', 'attendance_marked')
    list_filter = ('scope', 'result', 'attendance_marked')
    readonly_fields = ('checked_at',)
