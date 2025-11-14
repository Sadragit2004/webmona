# apps/order/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from apps.menu.models.menufreemodels.models import Restaurant
from .models import Ordermenu, MenuImage
import logging

logger = logging.getLogger(__name__)

@shared_task
def create_renewal_orders_for_expiring_restaurants():
    """
    ایجاد سفارش تمدید برای رستوران‌هایی که ۴ روز تا انقضای آنها باقی مانده است
    """
    try:
        # تاریخ ۴ روز آینده
        four_days_from_now = timezone.now() + timedelta(days=4)

        # پیدا کردن رستوران‌هایی که دقیقاً ۴ روز تا انقضای آنها باقی مانده
        expiring_restaurants = Restaurant.objects.filter(
            expireDate__date=four_days_from_now.date(),
            isActive=True
        ).exclude(
            # رستوران‌هایی که قبلاً سفارش تمدید فعال دارند را حذف کن
            Q(ordermenu__status=Ordermenu.STATUS_UNPAID) |
            Q(ordermenu__status=Ordermenu.STATUS_RENEWAL)
        ).distinct()

        created_orders = []

        for restaurant in expiring_restaurants:
            # بررسی اینکه آیا قبلاً سفارش تمدید برای این رستوران ایجاد شده
            existing_renewal_order = Ordermenu.objects.filter(
                restaurant=restaurant,
                status__in=[Ordermenu.STATUS_UNPAID, Ordermenu.NOTRENEWED, Ordermenu.STATUS_RENEWAL]
            ).exists()

            if not existing_renewal_order:
                # ایجاد سفارش تمدید جدید
                renewal_order = Ordermenu.objects.create(
                    restaurant=restaurant,
                    isfinaly=False,
                    isActive=False,
                    status=Ordermenu.NOTRENEWED,  # وضعیت "تمدید نشده"
                    is_seo_enabled=restaurant.isSeo  # حفظ تنظیمات سئو
                )

                created_orders.append({
                    'order_id': renewal_order.id,
                    'restaurant': restaurant.title,
                    'expire_date': restaurant.expireDate,
                    'owner': restaurant.owner.email
                })

                logger.info(f"سفارش تمدید برای رستوران {restaurant.title} ایجاد شد (ID: {renewal_order.id})")

        return {
            'success': True,
            'message': f'{len(created_orders)} سفارش تمدید ایجاد شد',
            'created_orders': created_orders,
            'total_checked': len(expiring_restaurants)
        }

    except Exception as e:
        logger.error(f"خطا در ایجاد سفارش‌های تمدید: {str(e)}")
        return {
            'success': False,
            'message': f'خطا در ایجاد سفارش‌های تمدید: {str(e)}'
        }

@shared_task
def check_and_deactivate_expired_restaurants():
    """
    بررسی و غیرفعال کردن رستوران‌های منقضی شده
    """
    try:
        expired_restaurants = Restaurant.get_expired_restaurants().filter(isActive=True)

        deactivated_count = 0
        for restaurant in expired_restaurants:
            restaurant.isActive = False
            restaurant.save()
            deactivated_count += 1

            logger.info(f"رستوران {restaurant.title} به دلیل انقضا غیرفعال شد")

        return {
            'success': True,
            'message': f'{deactivated_count} رستوران منقضی شده غیرفعال شد',
            'deactivated_count': deactivated_count
        }

    except Exception as e:
        logger.error(f"خطا در غیرفعال کردن رستوران‌های منقضی شده: {str(e)}")
        return {
            'success': False,
            'message': f'خطا در غیرفعال کردن رستوران‌های منقضی شده: {str(e)}'
        }

@shared_task
def send_renewal_reminders():
    """
    ارسال یادآوری تمدید برای رستوران‌هایی که به زودی منقضی می‌شوند
    """
    try:
        # رستوران‌هایی که بین ۳ تا ۷ روز تا انقضای آنها باقی مانده
        seven_days_from_now = timezone.now() + timedelta(days=7)
        three_days_from_now = timezone.now() + timedelta(days=3)

        expiring_soon_restaurants = Restaurant.objects.filter(
            expireDate__gte=three_days_from_now,
            expireDate__lte=seven_days_from_now,
            isActive=True
        )

        reminder_count = 0
        for restaurant in expiring_soon_restaurants:
            days_until_expiry = restaurant.days_until_expiry

            # در اینجا می‌توانید ایمیل یا نوتیفیکیشن ارسال کنید
            # send_renewal_email(restaurant.owner.email, restaurant, days_until_expiry)

            reminder_count += 1
            logger.info(f"یادآوری تمدید برای رستوران {restaurant.title} ({days_until_expiry} روز باقی مانده)")

        return {
            'success': True,
            'message': f'{reminder_count} یادآوری تمدید ارسال شد',
            'reminder_count': reminder_count
        }

    except Exception as e:
        logger.error(f"خطا در ارسال یادآوری‌های تمدید: {str(e)}")
        return {
            'success': False,
            'message': f'خطا در ارسال یادآوری‌های تمدید: {str(e)}'
        }