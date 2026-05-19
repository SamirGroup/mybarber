import base64
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .models import CameraConfig, FaceCheckLog
from . import services


def _can_students(user):
    if user.is_superuser:
        return True
    return user.groups.filter(
        name__in=['students_agent', 'students_manager', 'enrollment_agent', 'enrollment_manager']
    ).exists()


def _can_hr(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name='hr').exists()


def _can_faceid(user, scope):
    if user.is_superuser:
        return True
    if scope in ('students', 'shared'):
        return _can_students(user) or _can_hr(user)
    if scope == 'hr':
        return _can_hr(user)
    return False


def _kiosk_context(request, scope):
    cameras = CameraConfig.objects.filter(scope=scope, is_active=True)
    default_cam = cameras.filter(is_default=True).first() or cameras.first()
    recent = FaceCheckLog.objects.filter(scope=scope).select_related('student', 'employee', 'camera')[:15]
    engine = services.face_engine_status()
    from .models import FaceProfile

    profile_counts = {
        'students': FaceProfile.objects.filter(person_type='student', is_active=True).count(),
        'employees': FaceProfile.objects.filter(person_type='employee', is_active=True).count(),
    }

    titles = {
        'students': "O'quvchilar — FACE ID davomat",
        'hr': 'Xodimlar — FACE ID davomat',
        'shared': 'Umumiy kirish — FACE ID (o\'quvchi + xodim)',
    }
    return {
        'scope': scope,
        'page_title': titles.get(scope, 'FACE ID'),
        'cameras': cameras,
        'default_camera': default_cam,
        'recent_logs': recent,
        'engine': engine,
        'profile_counts': profile_counts,
    }


@login_required
def kiosk_students(request):
    if not _can_faceid(request.user, 'students'):
        return redirect('login')
    return render(request, 'faceid/kiosk.html', _kiosk_context(request, 'students'))


@login_required
def kiosk_hr(request):
    if not _can_faceid(request.user, 'hr'):
        return redirect('login')
    return render(request, 'faceid/kiosk.html', _kiosk_context(request, 'hr'))


@login_required
def kiosk_shared(request):
    if not _can_faceid(request.user, 'shared'):
        return redirect('login')
    return render(request, 'faceid/kiosk.html', _kiosk_context(request, 'shared'))


@login_required
@require_GET
def api_status(request):
    return JsonResponse(services.face_engine_status())


@login_required
@require_GET
def api_cameras(request):
    scope = request.GET.get('scope', 'students')
    if not _can_faceid(request.user, scope):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)
    items = list(
        CameraConfig.objects.filter(scope=scope, is_active=True).values(
            'id', 'name', 'device_id', 'device_label', 'is_default'
        )
    )
    return JsonResponse({'cameras': items})


@login_required
@require_POST
def api_camera_save(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON xato'}, status=400)

    scope = data.get('scope', 'students')
    if not _can_faceid(request.user, scope):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)

    device_id = (data.get('device_id') or '').strip()
    device_label = (data.get('device_label') or '').strip()
    name = (data.get('name') or device_label or 'Web kamera').strip()[:120]
    set_default = bool(data.get('is_default', True))

    cam, _ = CameraConfig.objects.update_or_create(
        scope=scope,
        device_id=device_id or f'label:{device_label}',
        defaults={
            'name': name,
            'device_label': device_label,
            'is_active': True,
            'is_default': set_default,
            'created_by': request.user,
        },
    )
    if set_default:
        cam.is_default = True
        cam.save()

    return JsonResponse({
        'ok': True,
        'camera': {
            'id': cam.id,
            'name': cam.name,
            'device_id': cam.device_id,
            'device_label': cam.device_label,
            'is_default': cam.is_default,
        },
    })


@login_required
@require_POST
def api_recognize(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON xato'}, status=400)

    scope = data.get('scope', 'students')
    if not _can_faceid(request.user, scope):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)

    image_b64 = data.get('image', '')
    if ',' in image_b64:
        image_b64 = image_b64.split(',', 1)[1]
    try:
        image_bytes = base64.b64decode(image_b64)
    except Exception:
        return JsonResponse({'error': 'Rasm formati noto\'g\'ri'}, status=400)

    camera_id = data.get('camera_id')
    result = services.process_recognition(
        image_bytes,
        scope=scope,
        camera_id=camera_id,
    )
    return JsonResponse(result)


@login_required
@require_POST
def api_rebuild_profiles(request):
    if not (request.user.is_superuser or _can_students(request.user) or _can_hr(request.user)):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)
    stats = services.rebuild_all_profiles()
    return JsonResponse({'ok': True, 'stats': stats})


@login_required
@require_GET
def api_recent_logs(request):
    scope = request.GET.get('scope', 'students')
    if not _can_faceid(request.user, scope):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)
    logs = FaceCheckLog.objects.filter(scope=scope).select_related('student', 'employee')[:20]
    items = []
    for log in logs:
        name = ''
        if log.student_id:
            name = log.student.full_name
        elif log.employee_id:
            name = log.employee.name
        items.append({
            'id': log.id,
            'result': log.result,
            'name': name,
            'person_type': log.person_type,
            'message': log.message,
            'attendance_marked': log.attendance_marked,
            'checked_at': log.checked_at.isoformat(),
        })
    return JsonResponse({'logs': items})
