from django.db import models
from apps.menu.models.menufreemodels.models import Restaurant
import utils
from django.utils import timezone


# apps/order/models.py
from django.db import models
from apps.menu.models.menufreemodels.models import Restaurant
import utils
from django.utils import timezone
from decimal import Decimal

class Ordermenu(models.Model):
    STATUS_UNPAID = 1
    STATUS_PAID = 2
    STATUS_CONFIRMED = 3
    STATUS_DELIVERED = 4
    STATUS_RENEWAL = 5
    NOTRENEWED = 6

    STATUS_CHOICES = [
        (STATUS_UNPAID, 'پرداخت نشده'),
        (STATUS_PAID, 'پرداخت شده'),
        (STATUS_CONFIRMED, 'تایید شده'),
        (STATUS_DELIVERED, 'تحویل شده'),
        (NOTRENEWED, 'تمدید نشده'),
        (STATUS_RENEWAL, 'تمدید شده'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name='رستوران')
    isfinaly = models.BooleanField(default=True, verbose_name='نهایی')
    isActive = models.BooleanField(default=False, verbose_name='فعال')
    imageFile = utils.FileUpload('images', 'ordermenu')
    image = models.ImageField(upload_to=imageFile.upload_to, verbose_name='عکس', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    # ✅ وضعیت سفارش
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES,
        default=STATUS_UNPAID,
        verbose_name='وضعیت سفارش'
    )

    # ✅ گزینه سئو (اگر کاربر بخواهد منو سئو شود)
    is_seo_enabled = models.BooleanField(default=False, verbose_name='سئوی منو فعال شود؟')

    # ✅ فیلدهای قیمت داینامیک
    base_price = models.PositiveIntegerField(default=990000, verbose_name="قیمت پایه (ریال)")
    seo_extra_price = models.PositiveIntegerField(default=390000, verbose_name="قیمت اضافه سئو (ریال)")
    final_price = models.PositiveIntegerField(default=0, verbose_name="قیمت نهایی (ریال)")

    def save(self, *args, **kwargs):
        # محاسبه قیمت نهایی قبل از ذخیره
        self.final_price = self.base_price
        if self.is_seo_enabled:
            self.final_price += self.seo_extra_price

        super().save(*args, **kwargs)

    def get_fixed_price(self):
        """تابع برای بازگرداندن مبلغ نهایی"""
        return self.final_price

    def get_price_display(self):
        """نمایش قیمت به صورت فرمت شده"""
        return f"{self.final_price // 10:,} تومان"

    def get_base_price_display(self):
        """نمایش قیمت پایه به صورت فرمت شده"""
        return f"{self.base_price // 10:,} تومان"

    def get_seo_price_display(self):
        """نمایش قیمت سئو به صورت فرمت شده"""
        return f"{self.seo_extra_price // 10:,} تومان"

    @classmethod
    def get_status_choices(cls):
        """تابع برای دسترسی به choicesهای وضعیت"""
        return cls.STATUS_CHOICES

    def get_status_info(self):
        """اطلاعات کامل وضعیت سفارش"""
        status_info = {
            'code': self.status,
            'display': self.get_status_display(),
            'is_paid': self.status in [self.STATUS_PAID, self.STATUS_CONFIRMED, self.STATUS_DELIVERED, self.STATUS_RENEWAL],
            'is_completed': self.status in [self.STATUS_DELIVERED, self.STATUS_RENEWAL],
            'is_pending': self.status in [self.STATUS_UNPAID, self.NOTRENEWED],
            'is_confirmed': self.status == self.STATUS_CONFIRMED,
            'is_delivered': self.status == self.STATUS_DELIVERED,
        }
        return status_info

    def __str__(self):
        return f"سفارش {self.id} از {self.restaurant} - {self.get_status_display()}"

    class Meta:
        verbose_name = 'سفارش منو'
        verbose_name_plural = 'سفارشات منو'


class MenuImage(models.Model):
    order = models.ForeignKey(Ordermenu, on_delete=models.CASCADE, related_name='images', verbose_name='سفارش')
    image = models.ImageField(upload_to='menu_images/', verbose_name='عکس منو')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='تاریخ آپلود')

    def __str__(self):
        return f"عکس {self.id} - سفارش {self.order.id}"

    class Meta:
        verbose_name = 'عکس منو'
        verbose_name_plural = 'عکس‌های منو'



