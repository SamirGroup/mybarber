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
    path('call-centre/initiate/', views.call_initiate, name='enrollment_call_initiate'),

    # Twilio webhooks
    path('twilio/voice/', views.twilio_voice_webhook, name='enrollment_twilio_voice'),
    path('twilio/recording-status/', views.twilio_recording_status, name='enrollment_twilio_recording'),
    path('twilio/status-callback/', views.twilio_status_callback, name='enrollment_twilio_status'),
    path('twilio/token/', views.twilio_token, name='enrollment_twilio_token'),

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
