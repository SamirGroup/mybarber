from django.test import TestCase


class FaceidSmokeTests(TestCase):
    def test_app_import(self):
        from faceid import services

        status = services.face_engine_status()
        self.assertIn('available', status)
