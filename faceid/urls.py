from django.urls import path
from . import views

urlpatterns = [
    path('students/', views.kiosk_students, name='faceid_students'),
    path('hr/', views.kiosk_hr, name='faceid_hr'),
    path('shared/', views.kiosk_shared, name='faceid_shared'),
    path('api/status/', views.api_status, name='faceid_api_status'),
    path('api/cameras/', views.api_cameras, name='faceid_api_cameras'),
    path('api/cameras/save/', views.api_camera_save, name='faceid_api_camera_save'),
    path('api/recognize/', views.api_recognize, name='faceid_api_recognize'),
    path('api/rebuild/', views.api_rebuild_profiles, name='faceid_api_rebuild'),
    path('api/logs/', views.api_recent_logs, name='faceid_api_logs'),
]
