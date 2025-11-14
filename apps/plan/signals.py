# apps/plan/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import PlanOrder

@receiver(pre_save, sender=PlanOrder)
def set_expiry_date(sender, instance, **kwargs):
    """تنظیم خودکار تاریخ انقضا هنگام ایجاد سفارش"""
    if not instance.expiryDate and instance.plan:
        instance.expiryDate = timezone.now() + timezone.timedelta(days=instance.plan.expiryDays)