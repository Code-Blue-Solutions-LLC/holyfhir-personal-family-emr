from config.branding import APP_NAME, APP_SHORT_NAME
from .models import SystemSettings
from .themes import DEFAULT_THEME, theme_assets


def system_settings(request):
    try:
        settings = SystemSettings.get_solo()
    except Exception:
        settings = None

    app_lock_enabled = bool(settings and settings.app_lock_enabled)
    theme_key = settings.app_theme if settings else DEFAULT_THEME

    return {
        "holyfhir_app_name": APP_NAME,
        "holyfhir_app_short_name": APP_SHORT_NAME,
        "holyfhir_system_settings": settings,
        "holyfhir_theme": theme_assets(theme_key),
        "holyfhir_app_lock_enabled": app_lock_enabled,
        "holyfhir_lock_shortcut_enabled": bool(
            app_lock_enabled and settings.lock_shortcut_enabled
        ),
    }
