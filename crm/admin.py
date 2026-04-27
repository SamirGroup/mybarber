from django.contrib import admin
from .models import Client, Barber, Service, Booking, Payment

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'created_at']
    search_fields = ['full_name', 'phone', 'email']

@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'specialty', 'rating', 'is_active']
    list_filter = ['is_active', 'specialty']
    search_fields = ['full_name', 'phone']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['client', 'barber', 'service', 'date', 'time', 'status']
    list_filter = ['status', 'date']
    search_fields = ['client__full_name', 'barber__full_name']
    date_hierarchy = 'date'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'amount', 'payment_type', 'payment_date']
    list_filter = ['payment_type', 'payment_date']