# ----------------------------
# Management Command (برای اضافه کردن به فایل management/commands)
# ----------------------------
"""
برای اجرای خودکار بررسی انقضا، یک فایل مدیریتی ایجاد کنید:

در مسیر: management/commands/check_restaurant_expiration.py

from django.core.management.base import BaseCommand
from apps.restaurant.models import check_restaurants_expiration

class Command(BaseCommand):
    help = 'Check and update restaurant expiration status'

    def handle(self, *args, **options):
        result = check_restaurants_expiration()
        self.stdout.write(self.style.SUCCESS(result))
"""

# ----------------------------
# Utility Functions (برای استفاده راحت)
# ----------------------------

from .models.menufreemodels.models import Restaurant
from django.utils import timezone

class RestaurantManager:
    """کلاس کمکی برای مدیریت آسان رستوران‌ها"""

    @staticmethod
    def get_active_restaurants():
        """دریافت رستوران‌های فعال و منقضی نشده"""
        return Restaurant.objects.filter(isActive=True, is_expired=False)

    @staticmethod
    def get_expired_restaurants():
        """دریافت رستوران‌های منقضی شده"""
        return Restaurant.objects.filter(is_expired=True)

    @staticmethod
    def get_expiring_soon(days=7):
        """دریافت رستوران‌هایی که به زودی منقضی می‌شوند"""
        from datetime import timedelta
        threshold = timezone.now() + timedelta(days=days)
        return Restaurant.objects.filter(
            expire_date__lte=threshold,
            expire_date__gt=timezone.now(),
            is_expired=False
        )

    @staticmethod
    def create_restaurant_with_expiration(owner, title, days=30, **kwargs):
        """ایجاد رستوران جدید با تاریخ انقضا"""
        restaurant = Restaurant(owner=owner, title=title, **kwargs)
        restaurant.set_expiration(days)
        return restaurant

    @staticmethod
    def bulk_extend_restaurants(restaurant_ids, days=30):
        """تمدید دسته‌جمعی رستوران‌ها"""
        updated_count = 0
        for restaurant in Restaurant.objects.filter(id__in=restaurant_ids):
            restaurant.extend_expiration(days)
            updated_count += 1
        return f"تعداد {updated_count} رستوران تمدید شد"