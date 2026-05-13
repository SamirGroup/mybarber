from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='enrollment_dashboard'),

    # Leads
    path('leads/', views.lead_list, name='enrollment_lead_list'),
    path('leads/new/', views.lead_create, name='enrollment_lead_create'),
    path('leads/<int:pk>/', views.lead_detail, name='enrollment_lead_detail'),

    # Meta Lead webhook
    path('webhook/meta-lead/', views.meta_lead_webhook, name='enrollment_meta_webhook'),

    # Call Centre
    path('call-centre/', views.call_centre, name='enrollment_call_centre'),
    path('call/initiate/', views.call_initiate, name='enrollment_call_initiate'),
    path('call/end/', views.call_end, name='enrollment_call_end'),
    path('call/<int:call_id>/notes/', views.call_notes_update, name='enrollment_call_notes'),

    # API Endpoints
    path('api/customer-info/', views.api_customer_info, name='enrollment_api_customer_info'),
    path('api/agent-stats/', views.api_agent_stats, name='enrollment_api_agent_stats'),
    path('api/call-queue/', views.api_call_queue, name='enrollment_api_call_queue'),
    path('agent/status/', views.agent_status_update, name='enrollment_agent_status'),

    # Twilio webhooks
    path('twilio/voice/', views.twilio_voice_webhook, name='enrollment_twilio_voice'),
    path('twilio/recording-status/', views.twilio_recording_status, name='enrollment_twilio_recording'),
    path('twilio/status-callback/', views.twilio_status_callback, name='enrollment_twilio_status'),
    path('twilio/token/', views.twilio_token, name='enrollment_twilio_token'),

    # O'zbekiston telefon kompaniyalari uchun SIP webhook (ixtiyoriy)
    path('sip/webhook/', views.sip_webhook, name='enrollment_sip_webhook'),

    # Applications
    path('applications/', views.application_list, name='enrollment_application_list'),
    path('applications/new/', views.application_create, name='enrollment_application_create'),
    path('applications/new/<int:lead_id>/', views.application_create, name='enrollment_application_create'),
    path('applications/<int:pk>/', views.application_detail, name='enrollment_application_detail'),

    # Agent
    path('agent/', views.agent_profile, name='enrollment_agent_profile'),

    # Reports
    path('reports/', views.reports, name='enrollment_reports'),
]
