from django.db import models
from apps.menu.models.menufreemodels.models import Restaurant
import utils
from django.utils import timezone

class Ordermenu(models.Model):
    STATUS_UNPAID = 1
    STATUS_PAID = 2
    STATUS_CONFIRMED = 3
    STATUS_DELIVERED = 4

    STATUS_CHOICES = [
        (STATUS_UNPAID, 'پرداخت نشده'),
        (STATUS_PAID, 'پرداخت شده'),
        (STATUS_CONFIRMED, 'تایید شده'),
        (STATUS_DELIVERED, 'تحویل شده'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name='رستوران')
    isfinaly = models.BooleanField(default=True, verbose_name='نهایی')
    isActive = models.BooleanField(default=False, verbose_name='فعال')
    imageFile = utils.FileUpload('images', 'ordermenu')
    image = models.ImageField(upload_to=imageFile.upload_to, verbose_name='عکس', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    # ✅ اضافه کردن فیلد وضعیت
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES,
        default=STATUS_UNPAID,
        verbose_name='وضعیت سفارش'
    )

    def get_fixed_price(self):
        """تابع برای بازگرداندن مبلغ ثابت 99,000 تومان"""
        return 99000*10

    @classmethod
    def get_status_choices(cls):
        """تابع برای دسترسی به choicesهای وضعیت"""
        return cls.STATUS_CHOICES

    def __str__(self):
        return f"سفارش {self.id} از {self.restaurant}"


class MenuImage(models.Model):
    order = models.ForeignKey(Ordermenu, on_delete=models.CASCADE, related_name='images', verbose_name='سفارش')
    image = models.ImageField(upload_to='menu_images/', verbose_name='عکس منو')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='تاریخ آپلود')

    def __str__(self):
        return f"عکس {self.id} - سفارش {self.order.id}"

    class Meta:
        verbose_name = 'عکس منو'
        verbose_name_plural = 'عکس‌های منو'
