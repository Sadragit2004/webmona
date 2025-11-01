from django.db import models
from apps.menu.models.menufreemodels.models import Restaurant
import utils

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
    image = models.ImageField(upload_to=imageFile.upload_to, verbose_name='عکس')
    # فیلد status حذف شده و فقط به عنوان ثابت تعریف می‌شود

    def get_fixed_price(self):
        """
        تابع برای بازگرداندن مبلغ ثابت 99,000 تومان
        """
        return 99000

    def get_status_display(self, status_value):
        """
        تابع برای نمایش متن وضعیت بر اساس مقدار عددی
        """
        for value, display in self.STATUS_CHOICES:
            if value == status_value:
                return display
        return "نامشخص"

    @classmethod
    def get_status_choices(cls):
        """
        تابع برای دسترسی به choicesهای وضعیت
        """
        return cls.STATUS_CHOICES