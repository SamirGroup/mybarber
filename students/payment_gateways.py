# Online to'lov tizimlari integratsiyasi
# Qo'llab-quvvatlanadi: Payme, Click, Uzum Bank, Apelsin, Humo, Uzcard
import hashlib
import hmac
import requests
import json
from decimal import Decimal
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import OnlinePayment, Payment, Student, Contract
from django.utils import timezone
from accounting.models import PaymentGateway
from accounting.services import record_income
from accounting.models import CashRegister, Account, JournalEntry, JournalLine
from decimal import Decimal


# ── Payme ──────────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def payme_webhook(request):
    """
    Payme webhook handler
    Docs: https://developer.help.paycom.uz/
    """
    try:
        data = json.loads(request.body)
        method = data.get('method')
        params = data.get('params', {})
        
        # Payme authentication
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        # TODO: Verify auth_header with PAYME_KEY
        
        if method == 'CheckPerformTransaction':
            # To'lov amalga oshirish mumkinligini tekshirish
            account = params.get('account', {})
            student_id = account.get('student_id')
            amount = params.get('amount', 0) / 100  # Payme tiyin da yuboradi
            
            try:
                student = Student.objects.get(id=student_id)
                return JsonResponse({'result': {'allow': True}})
            except Student.DoesNotExist:
                return JsonResponse({'error': {'code': -31050, 'message': 'Student not found'}})
        
        elif method == 'CreateTransaction':
            # Tranzaksiya yaratish
            transaction_id = params.get('id')
            account = params.get('account', {})
            student_id = account.get('student_id')
            amount = params.get('amount', 0) / 100
            
            online_payment, created = OnlinePayment.objects.get_or_create(
                transaction_id=transaction_id,
                defaults={
                    'provider': 'payme',
                    'student_id': student_id,
                    'amount': amount,
                    'status': 'pending',
                    'raw_request': data,
                }
            )
            
            return JsonResponse({
                'result': {
                    'create_time': int(online_payment.created_at.timestamp() * 1000),
                    'transaction': str(online_payment.id),
                    'state': 1,
                }
            })
        
        elif method == 'PerformTransaction':
            # To'lovni tasdiqlash
            transaction_id = params.get('id')
            
            try:
                online_payment = OnlinePayment.objects.get(transaction_id=transaction_id)
                online_payment.status = 'paid'
                online_payment.confirmed_at = timezone.now()
                online_payment.save()
                
                # Payment yaratish
                if not online_payment.payment:
                    payment = Payment.objects.create(
                        student=online_payment.student,
                        contract=online_payment.contract,
                        amount=online_payment.amount,
                        method='payme',
                        payment_date=timezone.now().date(),
                        month_for=online_payment.month_for or timezone.now().date(),
                        transaction_id=transaction_id,
                        is_confirmed=True,
                    )
                    online_payment.payment = payment
                    online_payment.save()
                
                return JsonResponse({
                    'result': {
                        'transaction': str(online_payment.id),
                        'perform_time': int(online_payment.confirmed_at.timestamp() * 1000),
                        'state': 2,
                    }
                })
            except OnlinePayment.DoesNotExist:
                return JsonResponse({'error': {'code': -31003, 'message': 'Transaction not found'}})
        
        elif method == 'CancelTransaction':
            # To'lovni bekor qilish
            transaction_id = params.get('id')
            
            try:
                online_payment = OnlinePayment.objects.get(transaction_id=transaction_id)
                online_payment.status = 'cancelled'
                online_payment.save()
                
                # Agar payment yaratilgan bo'lsa, uni ham bekor qilish
                if online_payment.payment:
                    online_payment.payment.delete()
                
                return JsonResponse({
                    'result': {
                        'transaction': str(online_payment.id),
                        'cancel_time': int(timezone.now().timestamp() * 1000),
                        'state': -1,
                    }
                })
            except OnlinePayment.DoesNotExist:
                return JsonResponse({'error': {'code': -31003, 'message': 'Transaction not found'}})
        
        elif method == 'CheckTransaction':
            # Tranzaksiya holatini tekshirish
            transaction_id = params.get('id')
            
            try:
                online_payment = OnlinePayment.objects.get(transaction_id=transaction_id)
                state = 1 if online_payment.status == 'pending' else 2 if online_payment.status == 'paid' else -1
                
                return JsonResponse({
                    'result': {
                        'create_time': int(online_payment.created_at.timestamp() * 1000),
                        'perform_time': int(online_payment.confirmed_at.timestamp() * 1000) if online_payment.confirmed_at else 0,
                        'transaction': str(online_payment.id),
                        'state': state,
                    }
                })
            except OnlinePayment.DoesNotExist:
                return JsonResponse({'error': {'code': -31003, 'message': 'Transaction not found'}})
        
        return JsonResponse({'error': {'code': -32601, 'message': 'Method not found'}})
    
    except Exception as e:
        return JsonResponse({'error': {'code': -32400, 'message': str(e)}})


# ── Click ──────────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def click_webhook(request):
    """
    Click webhook handler
    Docs: https://docs.click.uz/
    """
    try:
        click_trans_id = request.POST.get('click_trans_id')
        service_id = request.POST.get('service_id')
        merchant_trans_id = request.POST.get('merchant_trans_id')
        amount = float(request.POST.get('amount', 0))
        action = int(request.POST.get('action', 0))
        error = int(request.POST.get('error', 0))
        sign_time = request.POST.get('sign_time')
        sign_string = request.POST.get('sign_string')
        
        # TODO: Verify sign_string
        
        if action == 0:
            # Prepare (to'lov tayyorlash)
            student_id = merchant_trans_id
            
            try:
                student = Student.objects.get(id=student_id)
                
                online_payment, created = OnlinePayment.objects.get_or_create(
                    transaction_id=click_trans_id,
                    defaults={
                        'provider': 'click',
                        'student': student,
                        'amount': amount,
                        'status': 'pending',
                        'order_id': merchant_trans_id,
                        'raw_request': dict(request.POST),
                    }
                )
                
                return JsonResponse({
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'merchant_prepare_id': online_payment.id,
                    'error': 0,
                    'error_note': 'Success',
                })
            except Student.DoesNotExist:
                return JsonResponse({
                    'error': -5,
                    'error_note': 'Student not found',
                })
        
        elif action == 1:
            # Complete (to'lovni tasdiqlash)
            try:
                online_payment = OnlinePayment.objects.get(transaction_id=click_trans_id)
                
                if error == 0:
                    online_payment.status = 'paid'
                    online_payment.confirmed_at = timezone.now()
                    online_payment.save()
                    
                    # Payment yaratish
                    if not online_payment.payment:
                        payment = Payment.objects.create(
                            student=online_payment.student,
                            contract=online_payment.contract,
                            amount=online_payment.amount,
                            method='click',
                            payment_date=timezone.now().date(),
                            month_for=online_payment.month_for or timezone.now().date(),
                            transaction_id=click_trans_id,
                            is_confirmed=True,
                        )
                        online_payment.payment = payment
                        online_payment.save()
                else:
                    online_payment.status = 'failed'
                    online_payment.save()
                
                return JsonResponse({
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'merchant_confirm_id': online_payment.id,
                    'error': 0,
                    'error_note': 'Success',
                })
            except OnlinePayment.DoesNotExist:
                return JsonResponse({
                    'error': -6,
                    'error_note': 'Transaction not found',
                })
        
        return JsonResponse({'error': -8, 'error_note': 'Invalid action'})
    
    except Exception as e:
        return JsonResponse({'error': -9, 'error_note': str(e)})


# ── Uzum Bank ─────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def uzum_webhook(request):
    """
    Uzum Bank webhook handler
    """
    try:
        data = json.loads(request.body)
        
        transaction_id = data.get('transactionId')
        order_id = data.get('orderId')
        amount = float(data.get('amount', 0)) / 100  # Uzum tiyin da yuboradi
        status = data.get('status')
        
        student_id = order_id.split('_')[0] if '_' in order_id else order_id
        
        try:
            student = Student.objects.get(id=student_id)
            
            online_payment, created = OnlinePayment.objects.get_or_create(
                transaction_id=transaction_id,
                defaults={
                    'provider': 'uzum',
                    'student': student,
                    'amount': amount,
                    'status': 'pending',
                    'order_id': order_id,
                    'raw_request': data,
                }
            )
            
            if status == 'CONFIRMED':
                online_payment.status = 'paid'
                online_payment.confirmed_at = timezone.now()
                online_payment.save()
                
                # Payment yaratish
                if not online_payment.payment:
                    payment = Payment.objects.create(
                        student=online_payment.student,
                        contract=online_payment.contract,
                        amount=online_payment.amount,
                        method='uzum',
                        payment_date=timezone.now().date(),
                        month_for=online_payment.month_for or timezone.now().date(),
                        transaction_id=transaction_id,
                        is_confirmed=True,
                    )
                    online_payment.payment = payment
                    online_payment.save()
            elif status == 'CANCELLED':
                online_payment.status = 'cancelled'
                online_payment.save()
            
            return JsonResponse({'success': True})
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
