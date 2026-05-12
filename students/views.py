from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import json
import os
from datetime import date, timedelta

from .models import (
    Classroom, Student, Parent, DocumentType, StudentDocument,
    Subject, Schedule, Quarter, DailyGrade, QuarterGrade,
    Attendance, Homework, Contract, Payment, SmsNotificationConfig, SmsLog,
    ChatGroup, ChatMessage
)
from enrollment.models import Lead, Grade, AcademicYear
from django.contrib.auth.models import User, Group


# ── Role helpers ──────────────────────────────────────────────────────
def _is_students_staff(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['students_agent', 'students_manager', 'enrollment_agent', 'enrollment_manager']).exists()


def students_required(view):
    return user_passes_test(_is_students_staff, login_url='login')(login_required(view))


def _ensure_students_groups():
    for name in ('students_agent', 'students_manager'):
        Group.objects.get_or_create(name=name)


# ── Dashboard ─────────────────────────────────────────────────────────
@login_required
@students_required
def dashboard(request):
    _ensure_students_groups()

    # Stats
    students_total = Student.objects.count()
    students_active = Student.objects.filter(is_active=True).count()
    students_in_classroom = Student.objects.exclude(classroom__isnull=True).count()

    classrooms_total = Classroom.objects.count()
    subjects_total = Subject.objects.count()
    contracts_total = Contract.objects.filter(is_active=True).count()

    # Debtors
    today = timezone.now().date()
    debtors = []
    for contract in Contract.objects.filter(is_active=True):
        paid = contract.payments.filter(payment_date__month=today.month, payment_date__year=today.year).aggregate(s=Sum('amount'))['s'] or 0
        if paid < contract.effective_fee:
            debtors.append({
                'contract': contract,
                'debt': contract.effective_fee - paid,
                'parents': contract.student.parents.all()
            })

    # Recent activities
    recent_students = Student.objects.select_related('classroom').order_by('-created_at')[:10]
    recent_payments = Payment.objects.select_related('student', 'contract').order_by('-payment_date')[:10]
    recent_homework = Homework.objects.select_related('classroom', 'subject').order_by('-due_date')[:5]

    # Upcoming birthdays
    today = timezone.now().date()
    upcoming_birthdays = Student.objects.filter(
        birth_date__month=today.month, birth_date__day=today.day
    )[:5]

    context = {
        'students_total': students_total,
        'students_active': students_active,
        'students_in_classroom': students_in_classroom,
        'classrooms_total': classrooms_total,
        'subjects_total': subjects_total,
        'contracts_total': contracts_total,
        'debtors': debtors,
        'recent_students': recent_students,
        'recent_payments': recent_payments,
        'recent_homework': recent_homework,
        'upcoming_birthdays': upcoming_birthdays,
        'page_title': 'O\'quvchilar bo\'limi',
    }
    return render(request, 'students/dashboard.html', context)


# ── Classrooms ────────────────────────────────────────────────────────
@login_required
@students_required
def classroom_list(request):
    year_id = request.GET.get('year')
    classrooms = Classroom.objects.select_related('grade', 'academic_year', 'homeroom_teacher').all()
    
    if year_id:
        classrooms = classrooms.filter(academic_year_id=year_id)
    
    academic_years = AcademicYear.objects.all()
    
    context = {
        'classrooms': classrooms,
        'academic_years': academic_years,
        'page_title': 'Sinf xonalari',
    }
    return render(request, 'students/classroom_list.html', context)


@login_required
@students_required
def classroom_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        grade_id = request.POST.get('grade')
        academic_year_id = request.POST.get('academic_year')
        homeroom_teacher_id = request.POST.get('homeroom_teacher') or None
        capacity = request.POST.get('capacity', 30)
        
        classroom = Classroom(
            name=name,
            grade_id=grade_id,
            academic_year_id=academic_year_id,
            homeroom_teacher_id=homeroom_teacher_id,
            capacity=capacity
        )
        classroom.save()
        
        messages.success(request, f'Sinf yaratildi: {classroom.name}')
        return redirect('students_classroom_list')
    
    grades = Grade.objects.all()
    academic_years = AcademicYear.objects.all()
    teachers = User.objects.filter(groups__name__in=['students_agent', 'students_manager', 'enrollment_agent', 'enrollment_manager']).distinct()
    
    context = {
        'grades': grades,
        'academic_years': academic_years,
        'teachers': teachers,
        'page_title': 'Yangi sinf yaratish',
    }
    return render(request, 'students/classroom_form.html', context)


@login_required
@students_required
def classroom_detail(request, pk):
    classroom = get_object_or_404(
        Classroom.objects.select_related('grade', 'academic_year', 'homeroom_teacher'),
        pk=pk
    )
    students = classroom.students.select_related('classroom').all()
    schedules = classroom.schedules.select_related('subject', 'teacher').all()
    homeworks = classroom.homeworks.select_related('subject', 'teacher').all()
    
    context = {
        'classroom': classroom,
        'students': students,
        'schedules': schedules,
        'homeworks': homeworks,
        'page_title': f'Sinf: {classroom.name}',
    }
    return render(request, 'students/classroom_detail.html', context)


# ── Students ──────────────────────────────────────────────────────────
@login_required
@students_required
def student_list(request):
    classroom_filter = request.GET.get('classroom')
    search = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'last_name')
    
    students = Student.objects.select_related('classroom').all()
    
    if classroom_filter:
        students = students.filter(classroom_id=classroom_filter)
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(passport_or_id__icontains=search) |
            Q(erp_number__icontains=search)
        )
    
    students = students.order_by(sort_by)
    
    paginator = Paginator(students, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    classrooms = Classroom.objects.all()
    
    context = {
        'page_obj': page_obj,
        'classrooms': classrooms,
        'classroom_filter': classroom_filter,
        'search': search,
        'sort_by': sort_by,
        'page_title': 'O\'quvchilar ro\'yxati',
    }
    return render(request, 'students/student_list.html', context)


@login_required
@students_required
def student_create(request):
    if request.method == 'POST':
        student = Student(
            first_name=request.POST.get('first_name', '').strip(),
            last_name=request.POST.get('last_name', '').strip(),
            middle_name=request.POST.get('middle_name', '').strip(),
            gender=request.POST.get('gender', 'M'),
            birth_date=request.POST.get('birth_date') or timezone.now().date(),
            passport_or_id=request.POST.get('passport_or_id', '').strip(),
            erp_number=request.POST.get('erp_number', '').strip(),
            address=request.POST.get('address', '').strip(),
            medical_notes=request.POST.get('medical_notes', '').strip(),
            is_active=request.POST.get('is_active') == 'on',
            classroom_id=request.POST.get('classroom') or None,
        )
        student.save()
        
        # Parents
        parent_ids = request.POST.getlist('parents')
        if parent_ids:
            student.parents.add(*parent_ids)
        
        messages.success(request, f'O\'quvchi yaratildi: {student.full_name}')
        return redirect('students_detail', pk=student.pk)
    
    classrooms = Classroom.objects.all()
    parents = Parent.objects.all()
    
    context = {
        'classrooms': classrooms,
        'parents': parents,
        'page_title': 'Yangi o\'quvchi',
    }
    return render(request, 'students/student_form.html', context)


@login_required
@students_required
def student_detail(request, pk):
    student = get_object_or_404(
        Student.objects.select_related('classroom'),
        pk=pk
    )
    
    # Documents
    documents = student.documents.select_related('doc_type', 'uploaded_by').all()
    doc_types = DocumentType.objects.all()
    
    # Grades
    daily_grades = student.daily_grades.select_related('subject', 'teacher').order_by('-date')[:20]
    quarter_grades = student.quarter_grades.select_related('subject', 'quarter', 'teacher').all()
    
    # Attendance
    attendance = student.attendances.select_related('subject', 'marked_by').order_by('-date')[:30]
    
    # Finance
    contracts = student.contracts.select_related().all()
    payments = student.payments.select_related('contract', 'received_by').order_by('-payment_date')[:20]
    
    # Homework
    homeworks = Homework.objects.filter(classroom=student.classroom).select_related('subject', 'teacher').order_by('-due_date')[:10]
    
    # Chat groups
    chat_groups = student.chat_groups.all()
    
    # Debt calculation
    today = timezone.now().date()
    total_debt = 0
    for contract in contracts.filter(is_active=True):
        paid = contract.payments.filter(
            payment_date__month=today.month,
            payment_date__year=today.year
        ).aggregate(s=Sum('amount'))['s'] or 0
        total_debt += contract.effective_fee - paid
    
    context = {
        'student': student,
        'documents': documents,
        'doc_types': doc_types,
        'daily_grades': daily_grades,
        'quarter_grades': quarter_grades,
        'attendance': attendance,
        'contracts': contracts,
        'payments': payments,
        'homeworks': homeworks,
        'chat_groups': chat_groups,
        'total_debt': total_debt,
        'page_title': f'O\'quvchi: {student.full_name}',
    }
    return render(request, 'students/student_detail.html', context)


@login_required
@students_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student.first_name = request.POST.get('first_name', '').strip()
        student.last_name = request.POST.get('last_name', '').strip()
        student.middle_name = request.POST.get('middle_name', '').strip()
        student.gender = request.POST.get('gender', 'M')
        student.birth_date = request.POST.get('birth_date') or student.birth_date
        student.passport_or_id = request.POST.get('passport_or_id', '').strip()
        student.erp_number = request.POST.get('erp_number', '').strip()
        student.address = request.POST.get('address', '').strip()
        student.medical_notes = request.POST.get('medical_notes', '').strip()
        student.is_active = request.POST.get('is_active') == 'on'
        student.classroom_id = request.POST.get('classroom') or None
        student.save()
        
        # Update parents
        parent_ids = request.POST.getlist('parents')
        student.parents.set(parent_ids)
        
        messages.success(request, f'O\'quvchi ma\'lumotlari yangilandi: {student.full_name}')
        return redirect('students_detail', pk=student.pk)
    
    classrooms = Classroom.objects.all()
    parents = Parent.objects.all()
    
    context = {
        'student': student,
        'classrooms': classrooms,
        'parents': parents,
        'page_title': f'O\'quvchini tahrirlash: {student.full_name}',
    }
    return render(request, 'students/student_form.html', context)


# ── Documents ─────────────────────────────────────────────────────────
@login_required
@students_required
def document_upload(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        doc_type_id = request.POST.get('doc_type')
        title = request.POST.get('title', '').strip()
        file = request.FILES.get('file')
        notes = request.POST.get('notes', '').strip()
        
        if file:
            doc = StudentDocument(
                student=student,
                doc_type_id=doc_type_id,
                title=title,
                file=file,
                uploaded_by=request.user,
                notes=notes
            )
            doc.save()
            messages.success(request, 'Hujjat yuklandi')
        else:
            messages.error(request, 'Fayl tanlanmadi')
    
    return redirect('students_detail', pk=pk)


@login_required
@students_required
def document_delete(request, doc_pk):
    doc = get_object_or_404(StudentDocument, pk=doc_pk)
    student_pk = doc.student.pk
    doc.delete()
    messages.success(request, 'Hujjat o\'chirildi')
    return redirect('students_detail', pk=student_pk)


@login_required
@students_required
def document_type_list(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_required = request.POST.get('is_required') == 'on'
        
        doc_type, created = DocumentType.objects.get_or_create(
            name=name,
            defaults={'is_required': is_required}
        )
        if not created:
            doc_type.is_required = is_required
            doc_type.save()
        
        messages.success(request, 'Hujjat turi saqlandi')
        return redirect('students_doc_types')
    
    doc_types = DocumentType.objects.all()
    context = {
        'doc_types': doc_types,
        'page_title': 'Hujjat turlari',
    }
    return render(request, 'students/document_type_list.html', context)


# ── Grades ────────────────────────────────────────────────────────────
@login_required
@students_required
def daily_grade_add(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        grade = request.POST.get('grade')
        comment = request.POST.get('comment', '').strip()
        
        DailyGrade.objects.create(
            student_id=student_id,
            subject_id=subject_id,
            teacher=request.user,
            grade=grade,
            comment=comment
        )
        messages.success(request, 'Kunlik baholar qo\'shildi')
        return redirect('students_daily_grade')
    
    students = Student.objects.all()
    subjects = Subject.objects.all()
    context = {
        'students': students,
        'subjects': subjects,
        'page_title': 'Kunlik baholar qo\'shish',
    }
    return render(request, 'students/daily_grade_form.html', context)


@login_required
@students_required
def quarter_grade_add(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        quarter_id = request.POST.get('quarter')
        grade = request.POST.get('grade')
        
        QuarterGrade.objects.update_or_create(
            student_id=student_id,
            subject_id=subject_id,
            quarter_id=quarter_id,
            defaults={'grade': grade, 'teacher': request.user}
        )
        messages.success(request, 'Chorak bahosi saqlandi')
        return redirect('students_quarter_grade')
    
    students = Student.objects.all()
    subjects = Subject.objects.all()
    quarters = Quarter.objects.select_related('academic_year').all()
    context = {
        'students': students,
        'subjects': subjects,
        'quarters': quarters,
        'page_title': 'Chorak baholar qo\'shish',
    }
    return render(request, 'students/quarter_grade_form.html', context)


@login_required
@students_required
def grade_results(request):
    student_id = request.GET.get('student')
    quarter_id = request.GET.get('quarter')
    
    students = Student.objects.all()
    quarters = Quarter.objects.select_related('academic_year').all()
    quarter_grades = QuarterGrade.objects.select_related('student', 'subject', 'quarter', 'teacher')
    
    if student_id:
        quarter_grades = quarter_grades.filter(student_id=student_id)
    if quarter_id:
        quarter_grades = quarter_grades.filter(quarter_id=quarter_id)
    
    # Calculate averages
    averages = quarter_grades.values('student__first_name', 'student__last_name').annotate(
        avg=Avg('grade')
    ).order_by('-avg')
    
    context = {
        'students': students,
        'quarters': quarters,
        'quarter_grades': quarter_grades,
        'averages': averages,
        'page_title': 'Baholar natijalari',
    }
    return render(request, 'students/grade_results.html', context)


# ── Attendance ────────────────────────────────────────────────────────
@login_required
@students_required
def attendance_mark(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        date_str = request.POST.get('date') or timezone.now().date().isoformat()
        status = request.POST.get('status', 'present')
        subject_id = request.POST.get('subject') or None
        note = request.POST.get('note', '').strip()
        
        Attendance.objects.update_or_create(
            student_id=student_id,
            date=date_str,
            subject_id=subject_id,
            defaults={'status': status, 'marked_by': request.user, 'note': note}
        )
        messages.success(request, 'Davomat saqlandi')
        return redirect('students_attendance')
    
    students = Student.objects.all()
    subjects = Subject.objects.all()
    context = {
        'students': students,
        'subjects': subjects,
        'page_title': 'Davomat belgilash',
    }
    return render(request, 'students/attendance_form.html', context)


# ── Homework ──────────────────────────────────────────────────────────
@login_required
@students_required
def homework_list(request):
    classroom_filter = request.GET.get('classroom')
    subject_filter = request.GET.get('subject')
    
    homeworks = Homework.objects.select_related('classroom', 'subject', 'teacher').all()
    
    if classroom_filter:
        homeworks = homeworks.filter(classroom_id=classroom_filter)
    if subject_filter:
        homeworks = homeworks.filter(subject_id=subject_filter)
    
    classrooms = Classroom.objects.all()
    subjects = Subject.objects.all()
    
    context = {
        'homeworks': homeworks,
        'classrooms': classrooms,
        'subjects': subjects,
        'page_title': 'Uy vazifalar',
    }
    return render(request, 'students/homework_list.html', context)


@login_required
@students_required
def homework_create(request):
    if request.method == 'POST':
        classroom_id = request.POST.get('classroom')
        subject_id = request.POST.get('subject')
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        due_date = request.POST.get('due_date')
        file = request.FILES.get('file')
        
        Homework.objects.create(
            classroom_id=classroom_id,
            subject_id=subject_id,
            teacher=request.user,
            title=title,
            description=description,
            due_date=due_date,
            file=file
        )
        messages.success(request, 'Uy vazifasi yaratildi')
        return redirect('students_homework_list')
    
    classrooms = Classroom.objects.all()
    subjects = Subject.objects.all()
    context = {
        'classrooms': classrooms,
        'subjects': subjects,
        'page_title': 'Yangi uy vazifasi',
    }
    return render(request, 'students/homework_form.html', context)


# ── Finance ───────────────────────────────────────────────────────────
@login_required
@students_required
def student_finance(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    contracts = student.contracts.select_related().all()
    payments = student.payments.select_related('contract', 'received_by').order_by('-payment_date')
    
    # Calculate balance
    total_paid = payments.aggregate(s=Sum('amount'))['s'] or 0
    total_fee = sum(c.effective_fee for c in contracts.filter(is_active=True))
    
    context = {
        'student': student,
        'contracts': contracts,
        'payments': payments,
        'total_paid': total_paid,
        'total_fee': total_fee,
        'balance': total_paid - total_fee,
        'page_title': f'O\'quvchi moliyasi: {student.full_name}',
    }
    return render(request, 'students/student_finance.html', context)


@login_required
@students_required
def payment_add(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        method = request.POST.get('method', 'cash')
        payment_date = request.POST.get('payment_date') or timezone.now().date()
        month_for = request.POST.get('month_for') or payment_date
        contract_id = request.POST.get('contract') or None
        note = request.POST.get('note', '').strip()
        
        Payment.objects.create(
            student=student,
            contract_id=contract_id,
            amount=amount,
            method=method,
            payment_date=payment_date,
            month_for=month_for,
            received_by=request.user,
            note=note
        )
        messages.success(request, 'To\'lov qo\'shildi')
        return redirect('students_finance', pk=pk)
    
    contracts = student.contracts.filter(is_active=True)
    context = {
        'student': student,
        'contracts': contracts,
        'page_title': 'Yangi to\'lov',
    }
    return render(request, 'students/payment_form.html', context)


@login_required
@students_required
def contract_add(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        contract_number = request.POST.get('contract_number', '').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None
        monthly_fee = request.POST.get('monthly_fee')
        discount_percent = request.POST.get('discount_percent', 0)
        discount_reason = request.POST.get('discount_reason', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        Contract.objects.create(
            student=student,
            contract_number=contract_number,
            start_date=start_date,
            end_date=end_date,
            monthly_fee=monthly_fee,
            discount_percent=discount_percent,
            discount_reason=discount_reason,
            notes=notes
        )
        messages.success(request, 'Shartnoma yaratildi')
        return redirect('students_finance', pk=pk)
    
    context = {
        'student': student,
        'page_title': 'Yangi shartnoma',
    }
    return render(request, 'students/contract_form.html', context)


# ── SMS ───────────────────────────────────────────────────────────────
@login_required
@students_required
def sms_config(request):
    config, _ = SmsNotificationConfig.objects.get_or_create()
    
    if request.method == 'POST':
        config.day_of_month = request.POST.get('day_of_month', 5)
        config.is_active = request.POST.get('is_active') == 'on'
        config.message_template = request.POST.get('message_template', config.message_template)
        config.save()
        messages.success(request, 'SMS sozlamalari saqlandi')
        return redirect('students_sms_config')
    
    context = {
        'config': config,
        'page_title': 'SMS sozlamalari',
    }
    return render(request, 'students/sms_config.html', context)


@login_required
@students_required
def sms_send_now(request):
    if request.method == 'POST':
        config = SmsNotificationConfig.objects.first()
        if not config or not config.is_active:
            messages.error(request, 'SMS tizimi faollashtirilmagan')
            return redirect('students_sms_config')
        
        today = timezone.now().date()
        debtors = []
        
        for contract in Contract.objects.filter(is_active=True):
            paid = contract.payments.filter(
                payment_date__month=today.month,
                payment_date__year=today.year
            ).aggregate(s=Sum('amount'))['s'] or 0
            
            if paid < contract.effective_fee:
                debt = contract.effective_fee - paid
                for parent in contract.student.parents.all():
                    debtors.append({
                        'parent': parent,
                        'student': contract.student,
                        'contract': contract,
                        'debt': debt,
                        'phone': parent.phone
                    })
        
        # Send SMS (Twilio or local SMS gateway)
        for d in debtors:
            message = config.message_template.format(
                parent_name=d['parent'].full_name,
                student_name=d['student'].full_name,
                contract_number=d['contract'].contract_number,
                debt_amount=d['debt']
            )
            
            # TODO: Real SMS sending via Twilio or local provider
            # For now, just log
            SmsLog.objects.create(
                parent=d['parent'],
                student=d['student'],
                contract=d['contract'],
                phone=d['phone'],
                message=message,
                debt_amount=d['debt'],
                is_sent=False,
                error='SMS not sent (test mode)'
            )
        
        messages.success(request, f'{len(debtors)} ta qarzdor ota-onaga SMS yuborishga yuborildi')
        return redirect('students_sms_logs')
    
    return redirect('students_sms_config')


@login_required
@students_required
def sms_logs(request):
    logs = SmsLog.objects.select_related('parent', 'student', 'contract').order_by('-sent_at')
    
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'page_title': 'SMS xabarnomalar logi',
    }
    return render(request, 'students/sms_logs.html', context)


# ── Chat ──────────────────────────────────────────────────────────────
@login_required
@students_required
def chat_list(request):
    chat_groups = ChatGroup.objects.select_related('created_by', 'classroom').all()
    
    context = {
        'chat_groups': chat_groups,
        'page_title': 'Chat guruhlar',
    }
    return render(request, 'students/chat_list.html', context)


@login_required
@students_required
def chat_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        classroom_id = request.POST.get('classroom') or None
        student_ids = request.POST.getlist('students')
        member_ids = request.POST.getlist('members')
        
        chat = ChatGroup.objects.create(
            name=name,
            created_by=request.user,
            classroom_id=classroom_id
        )
        
        if student_ids:
            chat.students.add(*student_ids)
        if member_ids:
            chat.members.add(*member_ids)
        
        messages.success(request, 'Chat guruh yaratildi')
        return redirect('students_chat_detail', pk=chat.pk)
    
    classrooms = Classroom.objects.all()
    students = Student.objects.all()
    members = User.objects.filter(groups__name__in=['students_agent', 'students_manager', 'enrollment_agent', 'enrollment_manager']).distinct()
    
    context = {
        'classrooms': classrooms,
        'students': students,
        'members': members,
        'page_title': 'Yangi chat guruh',
    }
    return render(request, 'students/chat_form.html', context)


@login_required
@students_required
def chat_detail(request, pk):
    chat = get_object_or_404(
        ChatGroup.objects.select_related('created_by', 'classroom'),
        pk=pk
    )
    messages_list = chat.messages.select_related('sender').order_by('sent_at')
    
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        file = request.FILES.get('file')
        
        if text or file:
            ChatMessage.objects.create(
                group=chat,
                sender=request.user,
                text=text,
                file=file
            )
            messages.success(request, 'Xabar yuborildi')
            return redirect('students_chat_detail', pk=pk)
    
    context = {
        'chat': chat,
        'messages': messages_list,
        'page_title': f'Chat: {chat.name}',
    }
    return render(request, 'students/chat_detail.html', context)


@login_required
@students_required
@require_POST
def chat_send(request, pk):
    chat = get_object_or_404(ChatGroup, pk=pk)
    text = request.POST.get('text', '').strip()
    file = request.FILES.get('file')
    
    if text or file:
        ChatMessage.objects.create(
            group=chat,
            sender=request.user,
            text=text,
            file=file
        )
        return JsonResponse({'status': 'ok'})
    
    return JsonResponse({'status': 'error', 'error': 'Empty message'}, status=400)


# ── Schedule ──────────────────────────────────────────────────────────
@login_required
@students_required
def schedule_list(request):
    classroom_filter = request.GET.get('classroom')
    
    schedules = Schedule.objects.select_related('classroom', 'subject', 'teacher').all()
    
    if classroom_filter:
        schedules = schedules.filter(classroom_id=classroom_filter)
    
    classrooms = Classroom.objects.all()
    
    context = {
        'schedules': schedules,
        'classrooms': classrooms,
        'page_title': 'Dars jadvali',
    }
    return render(request, 'students/schedule_list.html', context)


@login_required
@students_required
def schedule_create(request):
    if request.method == 'POST':
        classroom_id = request.POST.get('classroom')
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher') or None
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        Schedule.objects.create(
            classroom_id=classroom_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time
        )
        messages.success(request, 'Dars jadvali qo\'shildi')
        return redirect('students_schedule')
    
    classrooms = Classroom.objects.all()
    subjects = Subject.objects.all()
    teachers = User.objects.filter(groups__name__in=['students_agent', 'students_manager', 'enrollment_agent', 'enrollment_manager']).distinct()
    
    context = {
        'classrooms': classrooms,
        'subjects': subjects,
        'teachers': teachers,
        'page_title': 'Yangi dars jadvali',
    }
    return render(request, 'students/schedule_form.html', context)


# ── Subjects ──────────────────────────────────────────────────────────
@login_required
@students_required
def subject_list(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        
        Subject.objects.get_or_create(name=name, defaults={'code': code})
        messages.success(request, 'Fan qo\'shildi')
        return redirect('students_subjects')
    
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects,
        'page_title': 'Fanlar',
    }
    return render(request, 'students/subject_list.html', context)


# ── API endpoints ─────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def api_add_student(request):
    """Meta Lead orqali o'quvchi yaratish uchun API"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('phone'):
            return JsonResponse({'error': 'Telefon raqam kerak'}, status=400)
        
        # Check if parent exists
        parent, _ = Parent.objects.get_or_create(
            phone=data['phone'],
            defaults={
                'first_name': data.get('first_name', 'Noma\'lum'),
                'last_name': data.get('last_name', ''),
                'email': data.get('email', ''),
            }
        )
        
        # Create student
        student = Student.objects.create(
            first_name=data.get('child_first_name', 'Noma\'lum'),
            last_name=data.get('child_last_name', ''),
            birth_date=data.get('birth_date') or timezone.now().date(),
            gender=data.get('gender', 'M'),
            passport_or_id=data.get('passport_or_id', ''),
            erp_number=data.get('erp_number', ''),
            address=data.get('address', ''),
            medical_notes=data.get('medical_notes', ''),
        )
        student.parents.add(parent)
        
        # Link to lead if exists
        lead_id = data.get('lead_id')
        if lead_id:
            try:
                from enrollment.models import Lead
                lead = Lead.objects.get(pk=lead_id)
                lead.status = 'registered'
                lead.save()
            except Lead.DoesNotExist:
                pass
        
        return JsonResponse({
            'status': 'ok',
            'student_id': student.id,
            'student_name': student.full_name
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def api_send_sms(request):
    """SMS yuborish uchun API"""
    try:
        data = json.loads(request.body)
        phone = data.get('phone')
        message = data.get('message')
        
        if not phone or not message:
            return JsonResponse({'error': 'Telefon va xabar kerak'}, status=400)
        
        # TODO: Real SMS sending
        # For now, just log
        SmsLog.objects.create(
            phone=phone,
            message=message,
            is_sent=False,
            error='SMS not sent (test mode)'
        )
        
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
