from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Client(models.Model):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.phone}"
    
    @property
    def visit_count(self):
        return self.booking_set.filter(status='completed').count()
    
    @property
    def total_spent(self):
        from .models import Payment
        return Payment.objects.filter(booking__client=self, booking__status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or 0

class Barber(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    rating = models.FloatField(default=5.0)
    is_active = models.BooleanField(default=True)
    work_schedule = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.full_name
    
    @property
    def total_bookings(self):
        return self.booking_set.count()
    
    @property
    def completed_bookings(self):
        return self.booking_set.filter(status='completed').count()
    
    @property
    def total_revenue(self):
        from .models import Payment
        return Payment.objects.filter(booking__barber=self, booking__status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or 0

class Service(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in minutes")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ${self.price} - {self.duration}min"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.client.full_name} - {self.barber.full_name} - {self.date} {self.time}"
    
    class Meta:
        ordering = ['-date', 'time']

class Payment(models.Model):
    PAYMENT_TYPES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('online', 'Online'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Payment for {self.booking} - ${self.amount}"