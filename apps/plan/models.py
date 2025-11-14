from django.db import models
from django.utils.text import slugify
from django.urls import reverse
import utils
from apps.user.models import CustomUser
from django.utils import timezone

class Plan(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام پلن")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="اسلاگ")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات پلن")
    price = models.PositiveIntegerField(

        blank=True,
        null=True,
        verbose_name="قیمت پلن"
    )
  
    expiryDays = models.IntegerField(
        default=30,
        verbose_name="انقضای پلن (روز)"
    )
    isActive = models.BooleanField(default=True, verbose_name="فعال")
    createdAt = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updatedAt = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    isFavorit = models.BooleanField(default=False,verbose_name='محبوب ترین')

    class Meta:
        verbose_name = "پلن"
        verbose_name_plural = "پلن‌ها"
        ordering = ['price']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('plan_detail', kwargs={'slug': self.slug})

class PlanFeature(models.Model):
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='features',
        verbose_name="پلن"
    )
    title = models.CharField(max_length=255, verbose_name="عنوان ویژگی")
    value = models.CharField(max_length=255, verbose_name="مقدار ویژگی", blank=True, null=True)
    order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")
    isAvailable = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "ویژگی پلن"
        verbose_name_plural = "ویژگی‌های پلن"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.plan.name} - {self.title}"





class PlanOrder(models.Model):
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="پلن"
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='plan_orders',
        verbose_name="کاربر"
    )
    createdAt = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    finalPrice = models.PositiveIntegerField(verbose_name="قیمت نهایی")

    # فیلدهای اضافی که ممکن است مفید باشند:
    isPaid = models.BooleanField(default=False, verbose_name="پرداخت شده")
    paidAt = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ پرداخت")
    expiryDate = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ انقضا")
    trackingCode = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="کد رهگیری"
    )

    class Meta:
        verbose_name = "سفارش پلن"
        verbose_name_plural = "سفارشات پلن"
        ordering = ['-createdAt']
        indexes = [
            models.Index(fields=['user', 'createdAt']),
            models.Index(fields=['isPaid', 'createdAt']),
        ]



    def __str__(self):
        return f"{self.user} - {self.plan.name} - {self.finalPrice}"

    def save(self, *args, **kwargs):
        # اگر تاریخ انقضا تنظیم نشده و پلن مرتبط وجود دارد
        if not self.expiryDate and self.plan:
            from django.utils import timezone
            self.expiryDate = timezone.now() + timezone.timedelta(days=self.plan.expiryDays)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('plan_order_detail', kwargs={'pk': self.pk})

    @property
    def days_remaining(self):
        """تعداد روزهای باقی‌مانده از اعتبار پلن"""
        if self.expiryDate:
            from django.utils import timezone
            remaining = self.expiryDate - timezone.now()
            return max(0, remaining.days)
        return 0

    @property
    def is_expired(self):
        """آیا پلن منقضی شده است؟"""
        return self.days_remaining == 0


    @property
    def is_active(self):
        """آیا پلن فعال است؟"""
        return self.isPaid and not self.is_expired

    def activate_plan(self):
        """فعال‌سازی پلن"""
        if not self.isPaid:
            self.isPaid = True
            self.paidAt = timezone.now()
            self.save()