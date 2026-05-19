"""Yuz tanish va davomat yozish xizmatlari."""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Optional

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone

logger = logging.getLogger(__name__)

FACE_AVAILABLE = False
_face_recognition = None


def _load_face_lib():
    global FACE_AVAILABLE, _face_recognition
    if _face_recognition is not None:
        return FACE_AVAILABLE
    try:
        import face_recognition as fr

        _face_recognition = fr
        FACE_AVAILABLE = True
    except ImportError:
        FACE_AVAILABLE = False
        logger.warning('face_recognition o\'rnatilmagan. pip install face_recognition')
    return FACE_AVAILABLE


def face_engine_status() -> dict:
    ok = _load_face_lib()
    return {
        'available': ok,
        'library': 'face_recognition' if ok else None,
        'message': (
            "Yuz tanish tizimi tayyor"
            if ok
            else "face_recognition kutubxonasi kerak: pip install face_recognition"
        ),
    }


def encode_from_bytes(image_bytes: bytes) -> Optional[list[float]]:
    """Rasm baytlaridan bitta yuz encoding."""
    if not _load_face_lib():
        return None
    import numpy as np
    from PIL import Image

    fr = _face_recognition
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    arr = np.array(img)
    locations = fr.face_locations(arr, model='hog')
    if not locations:
        return None
    encodings = fr.face_encodings(arr, known_face_locations=locations)
    if not encodings:
        return None
    return [float(x) for x in encodings[0]]


def encode_from_file_field(file_field) -> Optional[list[float]]:
    if not file_field:
        return None
    try:
        with default_storage.open(file_field.name, 'rb') as f:
            return encode_from_bytes(f.read())
    except Exception as exc:
        logger.exception('Rasmdan encoding: %s', exc)
        return None


def _distance(a: list[float], b: list[float]) -> float:
    import math

    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def match_encoding(
    encoding: list[float],
    *,
    scope: str,
    tolerance: Optional[float] = None,
) -> tuple[Optional[str], Optional[object], float]:
    """
    scope: students | hr | shared
    Qaytadi: (person_type, model_instance, distance) yoki (None, None, inf)
    """
    from .models import FaceProfile

    tol = tolerance if tolerance is not None else getattr(settings, 'FACEID_TOLERANCE', 0.55)

    qs = FaceProfile.objects.filter(is_active=True).select_related('student', 'employee')
    if scope == 'students':
        qs = qs.filter(person_type=FaceProfile.PERSON_STUDENT, student__is_active=True)
    elif scope == 'hr':
        qs = qs.filter(person_type=FaceProfile.PERSON_EMPLOYEE, employee__status='active')
    # shared — barcha faol profillar

    best_dist = float('inf')
    best_type = None
    best_obj = None

    for profile in qs:
        if not profile.encoding:
            continue
        dist = _distance(encoding, profile.encoding)
        if dist < best_dist:
            best_dist = dist
            best_type = profile.person_type
            best_obj = profile.student if profile.person_type == FaceProfile.PERSON_STUDENT else profile.employee

    if best_dist <= tol and best_obj is not None:
        return best_type, best_obj, best_dist
    return None, None, best_dist


def enroll_person(person_type: str, obj) -> bool:
    """Student yoki Employee rasmdan FACE profil yaratadi."""
    from .models import FaceProfile

    photo = getattr(obj, 'photo', None)
    if not photo:
        return False
    encoding = encode_from_file_field(photo)
    if not encoding:
        return False

    defaults = {'encoding': encoding, 'is_active': True}
    if person_type == FaceProfile.PERSON_STUDENT:
        FaceProfile.objects.update_or_create(
            person_type=person_type,
            student=obj,
            defaults={**defaults, 'employee': None},
        )
    else:
        FaceProfile.objects.update_or_create(
            person_type=person_type,
            employee=obj,
            defaults={**defaults, 'student': None},
        )
    return True


def rebuild_all_profiles() -> dict:
    from students.models import Student
    from hr.models import Employee
    from .models import FaceProfile

    stats = {'students': 0, 'employees': 0, 'skipped': 0, 'errors': 0}
    if not _load_face_lib():
        return {**stats, 'error': 'face_recognition yo\'q'}

    for student in Student.objects.filter(is_active=True).exclude(photo=''):
        if student.photo:
            try:
                if enroll_person(FaceProfile.PERSON_STUDENT, student):
                    stats['students'] += 1
                else:
                    stats['skipped'] += 1
            except Exception:
                stats['errors'] += 1

    for emp in Employee.objects.filter(status='active').exclude(photo=''):
        if emp.photo:
            try:
                if enroll_person(FaceProfile.PERSON_EMPLOYEE, emp):
                    stats['employees'] += 1
                else:
                    stats['skipped'] += 1
            except Exception:
                stats['errors'] += 1

    return stats


def mark_student_attendance(student, *, note: str = 'FACE ID') -> bool:
    from students.models import Attendance

    today = timezone.localdate()
    att = Attendance.objects.filter(student=student, date=today, subject__isnull=True).first()
    if att:
        att.status = 'present'
        att.note = note[:200]
        att.save(update_fields=['status', 'note'])
        return False
    Attendance.objects.create(
        student=student,
        date=today,
        subject=None,
        status='present',
        note=note[:200],
    )
    return True


def mark_employee_attendance(employee, *, note: str = 'FACE ID') -> bool:
    from hr.models import DailyReport

    today = timezone.localdate()
    now = timezone.localtime().time()
    shift = employee.shift
    report, created = DailyReport.objects.update_or_create(
        employee=employee,
        date=today,
        shift=shift,
        defaults={
            'was_present': True,
            'check_in': now,
            'notes': note[:200] if note else '',
        },
    )
    if not created and not report.check_in:
        report.check_in = now
        report.was_present = True
        report.save(update_fields=['check_in', 'was_present'])
    return created


def process_recognition(
    image_bytes: bytes,
    *,
    scope: str,
    camera_id: Optional[int] = None,
    cooldown_seconds: Optional[int] = None,
) -> dict:
    """
    Rasmni tahlil qiladi, bazadan tekshiradi, davomat yozadi.
    """
    from .models import CameraConfig, FaceCheckLog, FaceProfile

    if cooldown_seconds is None:
        cooldown_seconds = getattr(settings, 'FACEID_COOLDOWN_SECONDS', 45)

    engine = face_engine_status()
    if not engine['available']:
        log = FaceCheckLog.objects.create(
            camera_id=camera_id,
            scope=scope,
            result=FaceCheckLog.RESULT_ERROR,
            message=engine['message'],
        )
        return {
            'ok': False,
            'result': 'error',
            'message': engine['message'],
            'log_id': log.id,
        }

    encoding = encode_from_bytes(image_bytes)
    if encoding is None:
        log = FaceCheckLog.objects.create(
            camera_id=camera_id,
            scope=scope,
            result=FaceCheckLog.RESULT_NO_FACE,
            message='Kadrda yuz aniqlanmadi',
        )
        return {
            'ok': False,
            'result': 'no_face',
            'message': 'Kadrda yuz topilmadi. Kameraga to\'g\'ri qarang.',
            'log_id': log.id,
        }

    person_type, person_obj, distance = match_encoding(encoding, scope=scope)

    if person_type is None:
        log = FaceCheckLog.objects.create(
            camera_id=camera_id,
            scope=scope,
            result=FaceCheckLog.RESULT_UNKNOWN,
            confidence=distance if distance != float('inf') else None,
            message='Bazada mos yuz yo\'q',
        )
        return {
            'ok': False,
            'result': 'unknown',
            'message': 'Tanilmadi. Avval rasm yuklangan bo\'lishi kerak.',
            'distance': distance,
            'log_id': log.id,
        }

    # Cooldown — bir xil odamni qayta-qayta yozmaslik
    since = timezone.now() - timezone.timedelta(seconds=cooldown_seconds)
    if person_type == FaceProfile.PERSON_STUDENT:
        recent = FaceCheckLog.objects.filter(
            student=person_obj,
            result=FaceCheckLog.RESULT_MATCH,
            checked_at__gte=since,
            attendance_marked=True,
        ).exists()
    else:
        recent = FaceCheckLog.objects.filter(
            employee=person_obj,
            result=FaceCheckLog.RESULT_MATCH,
            checked_at__gte=since,
            attendance_marked=True,
        ).exists()

    if recent:
        name = getattr(person_obj, 'full_name', None) or getattr(person_obj, 'name', str(person_obj))
        log = FaceCheckLog.objects.create(
            camera_id=camera_id,
            scope=scope,
            person_type=person_type,
            student=person_obj if person_type == FaceProfile.PERSON_STUDENT else None,
            employee=person_obj if person_type == FaceProfile.PERSON_EMPLOYEE else None,
            result=FaceCheckLog.RESULT_MATCH,
            confidence=distance,
            attendance_marked=False,
            message=f'{name} — allaqachon belgilangan',
        )
        return {
            'ok': True,
            'result': 'already',
            'person_type': person_type,
            'name': name,
            'message': f'{name} bugun allaqachon davomatda',
            'log_id': log.id,
        }

    # Davomat yozish
    attendance_marked = False
    if person_type == FaceProfile.PERSON_STUDENT:
        mark_student_attendance(person_obj)
        name = person_obj.full_name
        section = "O'quvchilar davomadi"
    else:
        mark_employee_attendance(person_obj)
        name = person_obj.name
        section = 'HR xodimlar davomati'

    log = FaceCheckLog.objects.create(
        camera_id=camera_id,
        scope=scope,
        person_type=person_type,
        student=person_obj if person_type == FaceProfile.PERSON_STUDENT else None,
        employee=person_obj if person_type == FaceProfile.PERSON_EMPLOYEE else None,
        result=FaceCheckLog.RESULT_MATCH,
        confidence=distance,
        attendance_marked=True,
        message=f'{name} — {section}',
    )

    return {
        'ok': True,
        'result': 'matched',
        'person_type': person_type,
        'name': name,
        'section': section,
        'distance': round(distance, 3),
        'attendance_marked': True,
        'log_id': log.id,
    }
