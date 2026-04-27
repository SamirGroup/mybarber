from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Clients
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    
    # Barbers
    path('barbers/', views.barber_list, name='barber_list'),
    path('barbers/create/', views.barber_create, name='barber_create'),
    path('barbers/<int:pk>/edit/', views.barber_edit, name='barber_edit'),
    path('barbers/<int:pk>/', views.barber_detail, name='barber_detail'),
    
    # Services
    path('services/', views.service_list, name='service_list'),
    path('services/create/', views.service_create, name='service_create'),
    path('services/<int:pk>/edit/', views.service_edit, name='service_edit'),
    path('services/<int:pk>/delete/', views.service_delete, name='service_delete'),
    
    # Bookings
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/create/', views.booking_create, name='booking_create'),
    path('bookings/<int:pk>/edit/', views.booking_edit, name='booking_edit'),
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/status/', views.booking_status_update, name='booking_status_update'),
    
    # Payments
    path('payments/<int:booking_id>/create/', views.payment_create, name='payment_create'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # API
    path('api/available-slots/', views.api_available_slots, name='api_available_slots'),
    path('api/booking-stats/', views.api_booking_stats, name='api_booking_stats'),
]