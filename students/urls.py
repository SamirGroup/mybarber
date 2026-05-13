from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='students_dashboard'),

    # Classrooms
    path('classrooms/', views.classroom_list, name='students_classroom_list'),
    path('classrooms/new/', views.classroom_create, name='students_classroom_create'),
    path('classrooms/<int:pk>/', views.classroom_detail, name='students_classroom_detail'),
    path('classrooms/<int:pk>/journal/', views.classroom_journal, name='students_classroom_journal'),
    path('classrooms/<int:pk>/attendance/', views.attendance_by_date, name='students_classroom_attendance'),
    path('classrooms/<int:classroom_pk>/schedule/new/', views.schedule_create_for_classroom, name='students_schedule_create_for'),

    # Students
    path('list/', views.student_list, name='students_list'),
    path('new/', views.student_create, name='students_create'),
    path('<int:pk>/', views.student_detail, name='students_detail'),
    path('<int:pk>/edit/', views.student_edit, name='students_edit'),
    path('export/', views.export_students_excel, name='students_export'),
    path('import/', views.import_students_excel, name='students_import'),

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
    path('attendance/list/', views.attendance_list, name='students_attendance_list'),
    path('attendance/<int:pk>/edit/', views.attendance_edit, name='students_attendance_edit'),
    path('attendance/<int:pk>/delete/', views.attendance_delete, name='students_attendance_delete'),
    path('attendance/export/', views.export_attendance_excel, name='students_attendance_export'),

    # Homework
    path('homework/', views.homework_list, name='students_homework_list'),
    path('homework/new/', views.homework_create, name='students_homework_create'),

    # Finance
    path('<int:pk>/finance/', views.student_finance, name='students_finance'),
    path('<int:pk>/payment/add/', views.payment_add, name='students_payment_add'),
    path('<int:pk>/payment/init/', views.payment_init, name='students_payment_init'),
    path('<int:pk>/contract/add/', views.contract_add, name='students_contract_add'),
    path('payments/export/', views.export_payments_excel, name='students_payments_export'),
    path('online-payments/', views.online_payment_list, name='students_online_payments'),

    # Payment Gateway Webhooks
    path('webhook/payme/', views.payme_webhook, name='students_payme_webhook'),

    # SMS
    path('sms/config/', views.sms_config, name='students_sms_config'),
    path('sms/send-now/', views.sms_send_now, name='students_sms_send'),
    path('sms/logs/', views.sms_logs, name='students_sms_logs'),
    path('sms/daily-task/', views.sms_daily_task, name='students_sms_daily_task'),

    # Chat
    path('chat/', views.chat_list, name='students_chat_list'),
    path('chat/new/', views.chat_create, name='students_chat_create'),
    path('chat/<int:pk>/', views.chat_detail, name='students_chat_detail'),
    path('chat/<int:pk>/send/', views.chat_send, name='students_chat_send'),

    # Schedule CRUD
    path('schedule/', views.schedule_list, name='students_schedule'),
    path('schedule/new/', views.schedule_create, name='students_schedule_create'),
    path('schedule/<int:pk>/edit/', views.schedule_edit, name='students_schedule_edit'),
    path('schedule/<int:pk>/delete/', views.schedule_delete, name='students_schedule_delete'),

    # Lesson Periods
    path('lesson-periods/', views.lesson_period_list, name='students_lesson_periods'),
    path('lesson-periods/<int:pk>/edit/', views.lesson_period_edit, name='students_lesson_period_edit'),

    # Subjects
    path('subjects/', views.subject_list, name='students_subjects'),
]
