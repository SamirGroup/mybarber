from django.core.management.base import BaseCommand
from faceid import services


class Command(BaseCommand):
    help = "Barcha o'quvchi va xodim rasmlaridan FACE ID profillarini qayta yaratadi"

    def handle(self, *args, **options):
        stats = services.rebuild_all_profiles()
        if stats.get('error'):
            self.stderr.write(self.style.ERROR(stats['error']))
            return
        self.stdout.write(
            self.style.SUCCESS(
                f"O'quvchilar: {stats['students']}, Xodimlar: {stats['employees']}, "
                f"O'tkazildi: {stats['skipped']}, Xatolar: {stats['errors']}"
            )
        )
