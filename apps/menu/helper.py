from django.conf import settings
from .models.menufreemodels.models import Food, ExchangeRate

def get_current_exchange_rate():
    """دریافت نرخ ارز فعلی"""
    try:
        current_rate = ExchangeRate.objects.filter(is_active=True).first()
        if current_rate:
            return current_rate.rate
    except:
        pass
    return getattr(settings, 'EXCHANGE_RATE', 60000)

def update_all_food_prices():
    """به‌روزرسانی قیمت تمام غذاها بر اساس نرخ ارز فعلی"""
    try:
        current_rate = ExchangeRate.objects.filter(is_active=True).first()
        if current_rate:
            return current_rate.update_all_food_prices()
        return "No active exchange rate found"
    except Exception as e:
        return f"Error updating prices: {str(e)}"