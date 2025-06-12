from django.apps import AppConfig

class CalendarAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calendar_app'
    # ここで、models.py を直接インポートするような記述は、通常はしない