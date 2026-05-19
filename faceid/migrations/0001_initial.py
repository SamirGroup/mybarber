# Generated manually for faceid app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hr', '0008_add_absence_reason'),
        ('students', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CameraConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Masalan: Kirish eshigi, 1-sinf', max_length=120)),
                ('scope', models.CharField(choices=[('students', "O'quvchilar"), ('hr', 'Xodimlar (HR)'), ('shared', 'Umumiy kirish kamerasi')], default='students', max_length=20)),
                ('device_id', models.CharField(blank=True, help_text='navigator.mediaDevices deviceId (brauzerda saqlanadi)', max_length=512)),
                ('device_label', models.CharField(blank=True, max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['scope', '-is_default', 'name'],
            },
        ),
        migrations.CreateModel(
            name='FaceProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person_type', models.CharField(choices=[('student', "O'quvchi"), ('employee', 'Xodim')], max_length=20)),
                ('encoding', models.JSONField(help_text="128 o'lchamli yuz vektori")),
                ('is_active', models.BooleanField(default=True)),
                ('enrolled_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='face_profiles', to='hr.employee')),
                ('student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='face_profiles', to='students.student')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='FaceCheckLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scope', models.CharField(blank=True, max_length=20)),
                ('person_type', models.CharField(blank=True, max_length=20)),
                ('result', models.CharField(choices=[('matched', 'Tanildi'), ('unknown', "Noma'lum"), ('no_face', 'Yuz topilmadi'), ('error', 'Xato')], max_length=20)),
                ('confidence', models.FloatField(blank=True, help_text='Masofa (kichik = yaxshi)', null=True)),
                ('attendance_marked', models.BooleanField(default=False)),
                ('message', models.CharField(blank=True, max_length=255)),
                ('checked_at', models.DateTimeField(auto_now_add=True)),
                ('camera', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='faceid.cameraconfig')),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='face_checks', to='hr.employee')),
                ('student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='face_checks', to='students.student')),
            ],
            options={
                'ordering': ['-checked_at'],
            },
        ),
    ]
