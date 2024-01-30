from django.apps import AppConfig


class LynxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lynx'

    def ready(self):
        from . import signals
