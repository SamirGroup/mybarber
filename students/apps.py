from django.apps import AppConfig


class StudentsConfig(AppConfig):
    name = "students"
    
    def ready(self):
        # Signals ni import qilish
        import students.signals
