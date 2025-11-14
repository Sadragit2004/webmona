# models.py
from django.db import models
from django.utils import timezone

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام محصول")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="قیمت محصول")
    description = models.TextField(verbose_name="توضیحات محصول")
    is_active = models.BooleanField(default=True, verbose_name="وضعیت فعال")
    publish_date = models.DateTimeField(default=timezone.now, verbose_name="تاریخ انتشار")

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"

    def __str__(self):
        return self.name

class ProductFeature(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features', verbose_name="محصول")
    key = models.CharField(max_length=100, verbose_name="کلید")
    value = models.CharField(max_length=200, verbose_name="مقدار")
    slug = models.SlugField(max_length=100, verbose_name="اسلاگ")

    class Meta:
        verbose_name = "ویژگی محصول"
        verbose_name_plural = "ویژگی‌های محصول"

    def __str__(self):
        return f"{self.key}: {self.value}"

class ProductGallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery', verbose_name="محصول")
    image = models.ImageField(upload_to='products/gallery/', verbose_name="عکس")
    alt_text = models.CharField(max_length=200, verbose_name="متن جایگزین")
    is_active = models.BooleanField(default=True, verbose_name="وضعیت")

    class Meta:
        verbose_name = "عکس گالری"
        verbose_name_plural = "گالری محصولات"

    def __str__(self):
        return f"گالری {self.product.name}"