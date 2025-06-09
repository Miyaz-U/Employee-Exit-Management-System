# apps.py
from django.apps import AppConfig

class temsConfig(AppConfig):
    name = 'tems'

    def ready(self):
        import tems.signals
