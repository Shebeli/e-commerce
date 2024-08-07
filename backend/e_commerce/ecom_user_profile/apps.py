from django.apps import AppConfig


class EcomUserProfileConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ecom_user_profile"

    def ready(self):
        import ecom_user_profile.signals
