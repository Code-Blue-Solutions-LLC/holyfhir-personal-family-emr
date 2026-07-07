from django.templatetags.static import static

DEFAULT_THEME = "regular"

THEMES = {
    "regular": {
        "label": "Regular",
        "logo": "system_settings/themes/regular/HolyFHIR_Icon_256.png",
        "favicon": "system_settings/themes/regular/HolyFHIR_Favicon_128.png",
        "app_icon": "system_settings/themes/regular/HolyFHIR_AppIcon_1024.png",
        "master_logo": "system_settings/themes/regular/HolyFHIR_Logo_Master.png",
    },
    "cute": {
        "label": "Cute",
        "logo": "system_settings/themes/cute/HolyFHIR_Cute_Icon_256.png",
        "favicon": "system_settings/themes/cute/HolyFHIR_Cute_Favicon_128.png",
        "app_icon": "system_settings/themes/cute/HolyFHIR_Cute_AppIcon_1024.png",
        "master_logo": "system_settings/themes/cute/HolyFHIR_Cute_Master.png",
    },
}


THEME_CHOICES = tuple((key, theme["label"]) for key, theme in THEMES.items())


def theme_choices():
    return list(THEME_CHOICES)


def normalize_theme_key(theme_key):
    return theme_key if theme_key in THEMES else DEFAULT_THEME


def theme_assets(theme_key=None):
    key = normalize_theme_key(theme_key or DEFAULT_THEME)
    theme = THEMES[key]
    return {
        "key": key,
        "label": theme["label"],
        "logo_path": theme["logo"],
        "logo_url": static(theme["logo"]),
        "favicon_path": theme["favicon"],
        "favicon_url": static(theme["favicon"]),
        "app_icon_path": theme["app_icon"],
        "app_icon_url": static(theme["app_icon"]),
        "master_logo_path": theme["master_logo"],
        "master_logo_url": static(theme["master_logo"]),
    }
