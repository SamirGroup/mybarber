from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='students_dashboard'),

    # Classrooms
    path('classrooms/', views.classroom_list, name='students_classroom_list'),
    path('classrooms/new/', views.classroom_create, name='students_classroom_create'),
    path('classrooms/<int:pk>/', views.classroom_detail, name='students_classroom_detail'),

    # Students
    path('list/', views.student_list, name='students_list'),
    path('new/', views.student_create, name='students_create'),
    path('<int:pk>/', views.student_detail, name='students_detail'),
    path('<int:pk>/edit/', views.student_edit, name='students_edit'),

    # Documents
    path('<int:pk>/documents/upload/', views.document_upload, name='students_doc_upload'),
    path('documents/<int:doc_pk>/delete/', views.document_delete, name='students_doc_delete'),
    path('document-types/', views.document_type_list, name='students_doc_types'),

    # Grades
    path('grades/daily/', views.daily_grade_add, name='students_daily_grade'),
    path('grades/quarter/', views.quarter_grade_add, name='students_quarter_grade'),
    path('grades/results/', views.grade_results, name='students_grade_results'),

    # Attendance
    path('attendance/', views.attendance_mark, name='students_attendance'),

    # Homework
    path('homework/', views.homework_list, name='students_homework_list'),
    path('homework/new/', views.homework_create, name='students_homework_create'),

    # Finance
    path('<int:pk>/finance/', views.student_finance, name='students_finance'),
    path('<int:pk>/payment/add/', views.payment_add, name='students_payment_add'),
    path('<int:pk>/contract/add/', views.contract_add, name='students_contract_add'),

    # SMS
    path('sms/config/', views.sms_config, name='students_sms_config'),
    path('sms/send-now/', views.sms_send_now, name='students_sms_send'),
    path('sms/logs/', views.sms_logs, name='students_sms_logs'),

    # Chat
    path('chat/', views.chat_list, name='students_chat_list'),
    path('chat/new/', views.chat_create, name='students_chat_create'),
    path('chat/<int:pk>/', views.chat_detail, name='students_chat_detail'),
    path('chat/<int:pk>/send/', views.chat_send, name='students_chat_send'),

    # Schedule
    path('schedule/', views.schedule_list, name='students_schedule'),
    path('schedule/new/', views.schedule_create, name='students_schedule_create'),

    # Subjects
    path('subjects/', views.subject_list, name='students_subjects'),
]
