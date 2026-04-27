from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Client, Barber, Service, Booking, Payment
from .forms import ClientForm, BarberForm, ServiceForm, BookingForm, PaymentForm, DateRangeForm
from .decorators import admin_required, barber_or_admin_required
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

# @login_required
# def dashboard(request):
#     today = timezone.now().date()
    
#     # Stats
#     total_clients = Client.objects.count()
#     total_barbers = Barber.objects.filter(is_active=True).count()
#     total_services = Service.objects.filter(is_active=True).count()
    
#     today_bookings = Booking.objects.filter(date=today).count()
#     today_completed = Booking.objects.filter(date=today, status='completed').count()
#     today_pending = Booking.objects.filter(date=today, status='pending').count()
    
#     # Revenue
#     today_revenue = Payment.objects.filter(payment_date__date=today).aggregate(total=Sum('amount'))['total'] or 0
#     week_revenue = Payment.objects.filter(payment_date__date__gte=today - timedelta(days=7)).aggregate(total=Sum('amount'))['total'] or 0
#     month_revenue = Payment.objects.filter(payment_date__date__gte=today - timedelta(days=30)).aggregate(total=Sum('amount'))['total'] or 0
    
#     # Recent bookings
#     recent_bookings = Booking.objects.select_related('client', 'barber', 'service').order_by('-date', '-time')[:10]
    
#     # Popular services
#     popular_services = Service.objects.annotate(
#         booking_count=Count('booking')
#     ).order_by('-booking_count')[:5]
    
#     context = {
#         'total_clients': total_clients,
#         'total_barbers': total_barbers,
#         'total_services': total_services,
#         'today_bookings': today_bookings,
#         'today_completed': today_completed,
#         'today_pending': today_pending,
#         'today_revenue': today_revenue,
#         'week_revenue': week_revenue,
#         'month_revenue': month_revenue,
#         'recent_bookings': recent_bookings,
#         'popular_services': popular_services,
#     }
#     return render(request, 'dashboard.html', context)

@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # Stats
    total_clients = Client.objects.count()
    total_barbers = Barber.objects.filter(is_active=True).count()
    total_services = Service.objects.filter(is_active=True).count()
    
    today_bookings = Booking.objects.filter(date=today).count()
    today_completed = Booking.objects.filter(date=today, status='completed').count()
    today_pending = Booking.objects.filter(date=today, status='pending').count()
    
    # Revenue
    today_revenue = Payment.objects.filter(payment_date__date=today).aggregate(total=Sum('amount'))['total'] or 0
    week_revenue = Payment.objects.filter(payment_date__date__gte=today - timedelta(days=7)).aggregate(total=Sum('amount'))['total'] or 0
    month_revenue = Payment.objects.filter(payment_date__date__gte=today - timedelta(days=30)).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent bookings
    recent_bookings = Booking.objects.select_related('client', 'barber', 'service').order_by('-date', '-time')[:10]
    
    # Popular services
    popular_services = Service.objects.annotate(
        booking_count=Count('booking')
    ).order_by('-booking_count')[:5]
    
    context = {
        'total_clients': total_clients,
        'total_barbers': total_barbers,
        'total_services': total_services,
        'today_bookings': today_bookings,
        'today_completed': today_completed,
        'today_pending': today_pending,
        'today_revenue': today_revenue,
        'week_revenue': week_revenue,
        'month_revenue': month_revenue,
        'recent_bookings': recent_bookings,
        'popular_services': popular_services,
    }
    return render(request, 'dashboard.html', context)

# Client Views
@login_required
def client_list(request):
    clients = Client.objects.all().order_by('-created_at')
    search = request.GET.get('search', '')
    if search:
        clients = clients.filter(
            Q(full_name__icontains=search) | 
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    return render(request, 'clients/list.html', {'clients': clients, 'search': search})

@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client added successfully!')
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'clients/form.html', {'form': form, 'title': 'Add Client'})

@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client updated successfully!')
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'clients/form.html', {'form': form, 'title': 'Edit Client', 'client': client})

@admin_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Client deleted successfully!')
        return redirect('client_list')
    return render(request, 'clients/delete.html', {'client': client})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    bookings = client.booking_set.all().order_by('-date', '-time')
    return render(request, 'clients/detail.html', {'client': client, 'bookings': bookings})

# Barber Views
@login_required
@barber_or_admin_required
def barber_list(request):
    barbers = Barber.objects.all().order_by('-rating')
    search = request.GET.get('search', '')
    if search:
        barbers = barbers.filter(full_name__icontains=search)
    return render(request, 'barbers/list.html', {'barbers': barbers, 'search': search})

@admin_required
def barber_create(request):
    if request.method == 'POST':
        form = BarberForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Barber added successfully!')
            return redirect('barber_list')
    else:
        form = BarberForm()
    return render(request, 'barbers/form.html', {'form': form, 'title': 'Add Barber'})

@admin_required
def barber_edit(request, pk):
    barber = get_object_or_404(Barber, pk=pk)
    if request.method == 'POST':
        form = BarberForm(request.POST, instance=barber)
        if form.is_valid():
            form.save()
            messages.success(request, 'Barber updated successfully!')
            return redirect('barber_list')
    else:
        form = BarberForm(instance=barber)
    return render(request, 'barbers/form.html', {'form': form, 'title': 'Edit Barber', 'barber': barber})

@login_required
def barber_detail(request, pk):
    barber = get_object_or_404(Barber, pk=pk)
    bookings = barber.booking_set.all().order_by('-date', '-time')[:20]
    return render(request, 'barbers/detail.html', {'barber': barber, 'bookings': bookings})

# Service Views
@login_required
@barber_or_admin_required
def service_list(request):
    services = Service.objects.all().order_by('name')
    search = request.GET.get('search', '')
    if search:
        services = services.filter(name__icontains=search)
    return render(request, 'services/list.html', {'services': services, 'search': search})

@admin_required
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service added successfully!')
            return redirect('service_list')
    else:
        form = ServiceForm()
    return render(request, 'services/form.html', {'form': form, 'title': 'Add Service'})

@admin_required
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated successfully!')
            return redirect('service_list')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'services/form.html', {'form': form, 'title': 'Edit Service', 'service': service})

@admin_required
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service deleted successfully!')
        return redirect('service_list')
    return render(request, 'services/delete.html', {'service': service})

# Booking Views
@login_required
@barber_or_admin_required
def booking_list(request):
    bookings = Booking.objects.select_related('client', 'barber', 'service').order_by('-date', '-time')
    
    status = request.GET.get('status', '')
    if status:
        bookings = bookings.filter(status=status)
    
    date = request.GET.get('date', '')
    if date:
        bookings = bookings.filter(date=date)
    
    return render(request, 'bookings/list.html', {'bookings': bookings, 'status': status, 'date': date})

@login_required
def booking_create(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save()
            messages.success(request, 'Booking created successfully!')
            return redirect('booking_list')
    else:
        form = BookingForm()
    return render(request, 'bookings/form.html', {'form': form, 'title': 'Create Booking'})

@login_required
def booking_edit(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Booking updated successfully!')
            return redirect('booking_list')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'bookings/form.html', {'form': form, 'title': 'Edit Booking', 'booking': booking})

@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    payment = Payment.objects.filter(booking=booking).first()
    return render(request, 'bookings/detail.html', {'booking': booking, 'payment': payment})

@login_required
def booking_status_update(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.save()
            messages.success(request, f'Booking status updated to {new_status}!')
    return redirect('booking_detail', pk=pk)

# Payment Views
@login_required
def payment_create(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    
    if Payment.objects.filter(booking=booking).exists():
        messages.warning(request, 'Payment already recorded for this booking!')
        return redirect('booking_detail', pk=booking_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.booking = booking
            payment.save()
            booking.status = 'completed'
            booking.save()
            messages.success(request, 'Payment recorded successfully!')
            return redirect('booking_detail', pk=booking_id)
    else:
        form = PaymentForm(initial={'amount': booking.service.price})
    
    return render(request, 'payments/form.html', {'form': form, 'booking': booking, 'title': 'Record Payment'})

# Report Views
@login_required
@barber_or_admin_required
def reports(request):
    form = DateRangeForm(request.GET or None)
    
    today = timezone.now().date()
    start_date = request.GET.get('start_date', today - timedelta(days=30))
    end_date = request.GET.get('end_date', today)
    
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date', start_date)
        end_date = form.cleaned_data.get('end_date', end_date)
    
    # Revenue by day
    daily_revenue = Payment.objects.filter(
        payment_date__date__range=[start_date, end_date]
    ).extra({'date': "date(payment_date)"}).values('date').annotate(
        total=Sum('amount')
    ).order_by('date')
    
    # Revenue by payment type
    payment_by_type = Payment.objects.filter(
        payment_date__date__range=[start_date, end_date]
    ).values('payment_type').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Top barbers
    top_barbers = Barber.objects.filter(
        booking__payment__payment_date__date__range=[start_date, end_date]
    ).annotate(
        revenue=Sum('booking__payment__amount'),
        bookings_count=Count('booking')
    ).order_by('-revenue')[:5]
    
    # Top services
    top_services = Service.objects.filter(
        booking__payment__payment_date__date__range=[start_date, end_date]
    ).annotate(
        revenue=Sum('booking__payment__amount'),
        bookings_count=Count('booking')
    ).order_by('-revenue')[:5]
    
    # Top clients
    top_clients = Client.objects.filter(
        booking__payment__payment_date__date__range=[start_date, end_date]
    ).annotate(
        total_spent=Sum('booking__payment__amount'),
        visits=Count('booking')
    ).order_by('-total_spent')[:5]
    
    total_revenue = sum(item['total'] for item in daily_revenue)
    total_bookings = Booking.objects.filter(
        date__range=[start_date, end_date]
    ).count()
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'daily_revenue': daily_revenue,
        'payment_by_type': payment_by_type,
        'top_barbers': top_barbers,
        'top_services': top_services,
        'top_clients': top_clients,
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
    }
    
    return render(request, 'reports/index.html', context)

# API endpoints for AJAX
@login_required
def api_available_slots(request):
    barber_id = request.GET.get('barber_id')
    date = request.GET.get('date')
    
    if not barber_id or not date:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    # Get existing bookings for that barber on that date
    existing_bookings = Booking.objects.filter(
        barber_id=barber_id,
        date=date,
        status__in=['pending', 'confirmed']
    ).values_list('time', flat=True)
    
    # Available time slots (9 AM to 8 PM, hourly)
    all_slots = [f"{h:02d}:00" for h in range(9, 20)]
    available_slots = [slot for slot in all_slots if slot not in existing_bookings]
    
    return JsonResponse({'available_slots': available_slots})

@login_required
def api_booking_stats(request):
    today = timezone.now().date()
    
    stats = {
        'today_bookings': Booking.objects.filter(date=today).count(),
        'today_revenue': float(Payment.objects.filter(payment_date__date=today).aggregate(total=Sum('amount'))['total'] or 0),
        'total_clients': Client.objects.count(),
        'total_barbers': Barber.objects.filter(is_active=True).count(),
    }
    
    return JsonResponse(stats)