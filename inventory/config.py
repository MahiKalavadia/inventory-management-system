DEFAULT_LOW_STOCK_THRESHOLD = 5


def get_low_stock_threshold():
    try:
        from settings_app.models import SystemSettings
        return SystemSettings.load().low_stock_threshold
    except Exception:
        return DEFAULT_LOW_STOCK_THRESHOLD

