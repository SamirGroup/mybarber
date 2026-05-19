# O'zbekiston To'lov Tizimlari - API Integratsiyalari
# Qo'llab-quvvatlanadi: Payme, Click, Uzum Bank, Apelsin, Humo/UzCard, CAP

import hashlib
import hmac
import requests
import json
import base64
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings


class PaymentGatewayAPI:
    """Base class for payment gateways"""
    
    def __init__(self, gateway_config):
        """
        gateway_config: PaymentGateway model instance
        """
        self.gateway = gateway_config
        self.provider = gateway_config.provider
        self.is_test = gateway_config.is_test
        self.merchant_id = gateway_config.merchant_id
        self.api_key = gateway_config.api_key
        self.api_url = gateway_config.api_url
        self.commission_percent = gateway_config.commission_percent
    
    def calculate_commission(self, amount):
        """Hisoblash komissiya"""
        return (amount * self.commission_percent) / Decimal('100')
    
    def create_payment_url(self, student_id, amount, order_id, month_for=None, description=''):
        """
        To'lov URL yaratish - barcha provider'lar uchun abstract
        Returns: {'url': str, 'transaction_id': str, 'redirect_params': dict}
        """
        raise NotImplementedError("Subclass must implement this method")
    
    def verify_callback(self, data):
        """
        Webhook callback verification
        Returns: {'valid': bool, 'transaction_id': str, 'amount': Decimal, 'status': str}
        """
        raise NotImplementedError("Subclass must implement this method")


class PaymeAPI(PaymentGatewayAPI):
    """Payme Integratsiyasi"""
    
    def __init__(self, gateway_config):
        super().__init__(gateway_config)
        self.api_url = self.is_test and 'https://check.paycom.uz' or 'https://checkout.paycom.uz'
    
    def create_payment_url(self, student_id, amount, order_id, month_for=None, description=''):
        """
        Payme uchun to'lov sahifasini yaratish
        amount: so'mda
        """
        # Payme API call to create order
        params = {
            'method': 'CreateOrder',
            'id': 1,
            'params': {
                'merchant_id': self.merchant_id,
                'amount': int(amount * 100),  # Payme kopeykda
                'order_id': str(order_id),
                'account': {
                    'student_id': student_id,
                    'month_for': str(month_for) if month_for else '',
                },
                'callback_url': f"{settings.SITE_URL}/students/webhook/payme/",
            }
        }
        
        # Create signature
        sign_string = f"merchant_id={self.merchant_id}&amount={int(amount * 100)}&order_id={order_id}"
        signature = hmac.new(
            self.api_key.encode(),
            sign_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        params['params']['signature'] = signature
        
        # Return payment URL
        return {
            'url': f"https://checkout.paycom.uz/{self.merchant_id}",
            'transaction_id': str(order_id),
            'redirect_params': params
        }
    
    def verify_callback(self, data):
        """Payme webhook verification"""
        try:
            # Verify signature
            signature = data.pop('signature', '')
            sign_string = json.dumps(data, sort_keys=True)
            
            expected_signature = hmac.new(
                self.api_key.encode(),
                sign_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if signature != expected_signature:
                return {'valid': False, 'error': 'Invalid signature'}
            
            # Extract transaction info
            method = data.get('method', '')
            params = data.get('params', {})
            
            if method == 'CheckPerformTransaction':
                return {
                    'valid': True,
                    'action': 'check',
                    'transaction_id': params.get('id', ''),
                    'amount': Decimal(params.get('amount', 0)) / 100,
                }
            
            elif method == 'PerformTransaction':
                return {
                    'valid': True,
                    'action': 'confirm',
                    'transaction_id': params.get('id', ''),
                    'amount': Decimal(params.get('amount', 0)) / 100,
                }
            
            return {'valid': True, 'action': method, 'data': params}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}


class ClickAPI(PaymentGatewayAPI):
    """Click (UzCard) Integratsiyasi"""
    
    def create_payment_url(self, student_id, amount, order_id, month_for=None, description=''):
        """
        Click uchun to'lov sahifasini yaratish
        """
        # Click API requires service_id and merchant_account_id
        service_id = self.merchant_id
        merchant_account_id = self.api_key
        
        # Generate transaction ID
        transaction_id = f"CLICK_{order_id}_{int(timezone.now().timestamp())}"
        
        # Create payment URL
        base_url = "https://my.click.uz/services/pay"
        
        params = {
            'service_id': service_id,
            'merchant_account_id': merchant_account_id,
            'click_trans_id': transaction_id,
            'merchant_trans_id': str(order_id),
            'amount': int(amount * 100),  # kopeykda
            'action': 0,  # 0 = prepare payment
            'return_url': f"{settings.SITE_URL}/students/payment/complete/",
            'cancel_url': f"{settings.SITE_URL}/students/payment/cancel/",
        }
        
        # Create hash
        hash_string = f"{service_id};{merchant_account_id};{transaction_id};{int(amount * 100)};{order_id}"
        params['hash'] = hashlib.md5(hash_string.encode()).hexdigest()
        
        return {
            'url': base_url,
            'transaction_id': transaction_id,
            'redirect_params': params
        }
    
    def verify_callback(self, data):
        """Click webhook verification"""
        try:
            error = data.get('error', 0)
            click_trans_id = data.get('click_trans_id', '')
            merchant_trans_id = data.get('merchant_trans_id', '')
            
            if error != 0:
                return {
                    'valid': True,
                    'transaction_id': click_trans_id,
                    'status': 'failed',
                    'error': data.get('error_note', 'Unknown error')
                }
            
            return {
                'valid': True,
                'transaction_id': click_trans_id,
                'status': 'paid',
                'order_id': merchant_trans_id,
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}


class UzumBankAPI(PaymentGatewayAPI):
    """Uzum Bank Integratsiyasi"""
    
    def create_payment_url(self, student_id, amount, order_id, month_for=None, description=''):
        """
        Uzum Bank Merchant API orqali to'lov yaratish
        """
        transaction_id = f"UZUM_{order_id}_{int(timezone.now().timestamp())}"
        
        # Uzum Bank API endpoint
        api_url = self.is_test and 'https://api-sandbox.uzumbank.uz' or 'https://api.uzumbank.uz'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }
        
        payload = {
            'merchantId': self.merchant_id,
            'orderId': str(order_id),
            'amount': float(amount),
            'currency': 'UZS',
            'description': description or f"To'lov {student_id} uchun",
            'successUrl': f"{settings.SITE_URL}/students/payment/complete/",
            'errorUrl': f"{settings.SITE_URL}/students/payment/cancel/",
            'callbackUrl': f"{settings.SITE_URL}/students/webhook/uzum/",
        }
        
        try:
            response = requests.post(
                f"{api_url}/api/v1/payment/create",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                'url': result.get('paymentUrl'),
                'transaction_id': result.get('transactionId', transaction_id),
                'redirect_params': result
            }
        except Exception as e:
            return {'error': str(e)}
    
    def verify_callback(self, data):
        """Uzum Bank webhook verification"""
        try:
            status = data.get('status', '')
            transaction_id = data.get('transactionId', '')
            order_id = data.get('orderId', '')
            
            return {
                'valid': True,
                'transaction_id': transaction_id,
                'status': 'paid' if status == 'CONFIRMED' else status.lower(),
                'order_id': order_id,
                'amount': Decimal(str(data.get('amount', 0))),
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}


class ApelsinAPI(PaymentGatewayAPI):
    """Apelsin Integratsiyasi (Apelsin.uz)"""
    
    def create_payment_url(self, student_id, amount, order_id, month_for=None, description=''):
        """
        Apelsin payment URL yaratish
        """
        transaction_id = f"APELSIN_{order_id}_{int(timezone.now().timestamp())}"
        
        # Apelsin API endpoint
        api_url = self.is_test and 'https://api.sandbox.apelsin.uz' or 'https://api.apelsin.uz'
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'merchant_id': self.merchant_id,
            'order_id': str(order_id),
            'amount': float(amount),
            'currency': 'UZS',
            'description': description or f"To'lov {student_id} uchun",
            'success_url': f"{settings.SITE_URL}/students/payment/complete/",
            'fail_url': f"{settings.SITE_URL}/students/payment/cancel/",
            'callback_url': f"{settings.SITE_URL}/students/webhook/apelsin/",
            'user_data': {
                'student_id': student_id,
                'month_for': str(month_for) if month_for else '',
            }
        }
        
        try:
            response = requests.post(
                f"{api_url}/api/v1/payment/create",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                'url': result.get('payment_url'),
                'transaction_id': result.get('transaction_id', transaction_id),
                'redirect_params': result
            }
        except Exception as e:
            return {'error': str(e)}
    
    def verify_callback(self, data):
        """Apelsin webhook verification"""
        try:
            status = data.get('status', '')
            transaction_id = data.get('transaction_id', '')
            order_id = data.get('order_id', '')
            
            return {
                'valid': True,
                'transaction_id': transaction_id,
                'status': 'paid' if status in ['SUCCESS', 'COMPLETED'] else status.lower(),
                'order_id': order_id,
                'amount': Decimal(str(data.get('amount', 0))),
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}


class CAPAPI(PaymentGatewayAPI):
    """CAP (Click Aylama Pul) Integratsiyasi"""
    
    def create_payment_url(self, student_id, amount, order_id, month_for=None, description=''):
        """
        CAP orqali to'lov yaratish
        """
        transaction_id = f"CAP_{order_id}_{int(timezone.now().timestamp())}"
        
        # CAP API
        api_url = self.is_test and 'https://api-sandbox.cap.uz' or 'https://api.cap.uz'
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'merchant_id': self.merchant_id,
            'order_id': str(order_id),
            'amount': float(amount),
            'currency': 'UZS',
            'description': description or f"To'lov {student_id} uchun",
            'success_url': f"{settings.SITE_URL}/students/payment/complete/",
            'cancel_url': f"{settings.SITE_URL}/students/payment/cancel/",
            'callback_url': f"{settings.SITE_URL}/students/webhook/cap/",
            'metadata': {
                'student_id': student_id,
                'month_for': str(month_for) if month_for else '',
            }
        }
        
        try:
            response = requests.post(
                f"{api_url}/api/v1/payments/create",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                'url': result.get('payment_url'),
                'transaction_id': result.get('transaction_id', transaction_id),
                'redirect_params': result
            }
        except Exception as e:
            return {'error': str(e)}
    
    def verify_callback(self, data):
        """CAP webhook verification"""
        try:
            status = data.get('status', '')
            transaction_id = data.get('transaction_id', '')
            order_id = data.get('order_id', '')
            
            return {
                'valid': True,
                'transaction_id': transaction_id,
                'status': 'paid' if status == 'COMPLETED' else status.lower(),
                'order_id': order_id,
                'amount': Decimal(str(data.get('amount', 0))),
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}


class HumoUzcardAPI(PaymentGatewayAPI):
    """Humo/UzCard Integratsiyasi"""
    
    def create_payment_url(self, student_id, amount, order_id, month_for=None, description=''):
        """
        Humo/UzCard orqali to'lov yaratish
        """
        transaction_id = f"HUMO_{order_id}_{int(timezone.now().timestamp())}"
        
        # Humo/UzCard API
        api_url = self.is_test and 'https://api-sandbox.humo.uz' or 'https://api.humo.uz'
        
        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
        }
        
        payload = {
            'merchant_id': self.merchant_id,
            'order_id': str(order_id),
            'amount': int(amount * 100),  # kopeykda
            'currency': '860',  # UZS
            'description': description or f"To'lov {student_id} uchun",
            'success_url': f"{settings.SITE_URL}/students/payment/complete/",
            'cancel_url': f"{settings.SITE_URL}/students/payment/cancel/",
            'callback_url': f"{settings.SITE_URL}/students/webhook/humo/",
            'account': {
                'student_id': str(student_id),
                'month_for': str(month_for) if month_for else '',
            }
        }
        
        # Create signature
        sign_string = f"{self.merchant_id}{str(order_id)}{int(amount * 100)}{self.api_key}"
        payload['signature'] = hashlib.sha256(sign_string.encode()).hexdigest()
        
        try:
            response = requests.post(
                f"{api_url}/api/v1/payment/create",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                'url': result.get('payment_url'),
                'transaction_id': result.get('transaction_id', transaction_id),
                'redirect_params': result
            }
        except Exception as e:
            return {'error': str(e)}
    
    def verify_callback(self, data):
        """Humo/UzCard webhook verification"""
        try:
            status = data.get('status', '')
            transaction_id = data.get('transaction_id', '')
            order_id = data.get('order_id', '')
            
            return {
                'valid': True,
                'transaction_id': transaction_id,
                'status': 'paid' if status == 'SUCCESS' else status.lower(),
                'order_id': order_id,
                'amount': Decimal(str(data.get('amount', 0))) / 100,
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}


def get_gateway_api(provider):
    """
    Provider nomiga qarab API klassini qaytarish
    """
    from accounting.models import PaymentGateway
    
    try:
        gateway = PaymentGateway.objects.get(provider=provider, is_active=True)
        
        api_classes = {
            'payme': PaymeAPI,
            'payme_business': PaymeAPI,
            'click': ClickAPI,
            'uzum': UzumBankAPI,
            'apelsin': ApelsinAPI,
            'cap': CAPAPI,
            'humo': HumoUzcardAPI,
            'uzcard': HumoUzcardAPI,
        }
        
        api_class = api_classes.get(provider)
        if api_class:
            return api_class(gateway)
        
        return None
        
    except PaymentGateway.DoesNotExist:
        return None


def create_payment(provider_name, student_id, amount, order_id, month_for=None, description=''):
    """
    To'lov yaratish - avtomatik provider tanlash
    Returns: {'url': str, 'transaction_id': str, 'provider': str, 'error': str}
    """
    api = get_gateway_api(provider_name)
    
    if not api:
        return {'error': f'{provider_name} to\'lov tizimi topilmadi yoki faol emas'}
    
    result = api.create_payment_url(student_id, amount, order_id, month_for, description)
    
    if 'error' in result:
        return {'error': result['error']}
    
    return {
        'url': result.get('url'),
        'transaction_id': result.get('transaction_id'),
        'provider': provider_name,
        'redirect_params': result.get('redirect_params', {})
    }
