from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='cc_dashboard'),
    path('leads/', views.lead_list, name='cc_lead_list'),
    path('leads/<int:pk>/', views.lead_detail, name='cc_lead_detail'),
    path('leads/<int:pk>/status/', views.lead_update_status, name='cc_lead_status'),
    path('leads/<int:pk>/comment/', views.lead_add_comment, name='cc_lead_comment'),
    path('leads/<int:pk>/assign/', views.lead_assign, name='cc_lead_assign'),
    path('notifications/', views.notifications, name='cc_notifications'),
    path('notifications/count/', views.notifications_count, name='cc_notifications_count'),
    path('reports/', views.reports, name='cc_reports'),
    path('reports/export/', views.export_leads_excel, name='cc_export_excel'),
    path('users/', views.user_management, name='cc_users'),
    path('settings/', views.system_settings, name='cc_settings'),
    path('test-lead/', views.create_test_lead_view, name='cc_test_lead'),
    path('api/fetch-lead/', views.api_fetch_lead, name='cc_api_fetch_lead'),
    path('api/webhook/', views.meta_webhook, name='cc_meta_webhook'),
]
