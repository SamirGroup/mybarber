from django.urls import path
from . import views

urlpatterns = [
    path('', views.accounting_dashboard, name='accounting_dashboard'),
    path('students-payments/', views.students_payments_report, name='students_payments_report'),
]
