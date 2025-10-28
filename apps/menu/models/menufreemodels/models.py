import os
from uuid import uuid4
from decimal import Decimal
from django.db import models
from django.utils.text import slugify
from apps.user.models import CustomUser
from django.utils.translation import gettext as _
from django.conf import settings


# ----------------------------
# Base abstract model
# ----------------------------
class BaseModel(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True, verbose_name="عنوان فارسی")
    title_en = models.CharField(max_length=255, null=True, blank=True, verbose_name="عنوان انگلیسی")
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    isActive = models.BooleanField(default=True, null=True, blank=True)
    displayOrder = models.IntegerField(default=0, null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updatedAt = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['displayOrder']

    def save(self, *args, **kwargs):
        # ساخت اسلاگ بر اساس عنوان انگلیسی یا فارسی
        if not self.slug:
            base_title = self.title_en or self.title or "item"
            base_slug = slugify(base_title)
            slug = base_slug
            counter = 1
            while self.__class__.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or self.title_en or ''

    def get_title(self, lang='fa'):
        """دریافت عنوان بر اساس زبان"""
        if lang == 'en' and self.title_en:
            return self.title_en
        return self.title or self.title_en or ''

    def get_description(self, lang='fa'):
        """دریافت توضیحات بر اساس زبان"""
        if hasattr(self, 'description') and hasattr(self, 'description_en'):
            if lang == 'en' and self.description_en:
                return self.description_en
            return self.description or self.description_en or ''
        return ''


# ----------------------------
# Upload helpers
# ----------------------------
def upload_to_category(instance, filename):
    name, ext = os.path.splitext(filename)
    return f'categories/images/{uuid4()}{ext}'


def upload_to_restaurant_logo(instance, filename):
    name, ext = os.path.splitext(filename)
    return f'restaurants/logos/{uuid4()}{ext}'


def upload_to_restaurant_cover(instance, filename):
    name, ext = os.path.splitext(filename)
    return f'restaurants/covers/{uuid4()}{ext}'


def upload_to_menu_category(instance, filename):
    name, ext = os.path.splitext(filename)
    return f'restaurants/menu-categories/images/{uuid4()}{ext}'


def upload_to_food_image(instance, filename):
    name, ext = os.path.splitext(filename)
    return f'foods/images/{uuid4()}{ext}'


def upload_to_food_sound(instance, filename):
    name, ext = os.path.splitext(filename)
    return f'sound/menu/{uuid4()}{ext}'


# ----------------------------
# Exchange Rate
# ----------------------------
class ExchangeRate(models.Model):
    rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="نرخ برابری (تومان)")
    is_active = models.BooleanField(default=True, verbose_name="نرخ فعال")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'نرخ ارز'
        verbose_name_plural = 'نرخ‌های ارز'

    def save(self, *args, **kwargs):
        # غیرفعال کردن سایر نرخ‌ها
        if self.is_active:
            ExchangeRate.objects.filter(is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

        # به‌روزرسانی خودکار قیمت تمام غذاها
        if self.is_active:
            self.update_all_food_prices()

    def update_all_food_prices(self):
        """به‌روزرسانی قیمت تمام غذاها بر اساس این نرخ ارز"""
        try:
            foods = Food.objects.filter(price__isnull=False)
            updated_count = 0
            for food in foods:
                food.update_usd_price(self.rate)
                food.save(update_fields=['price_usd_cents'])
                updated_count += 1
            return f"تعداد {updated_count} غذا با نرخ {self.rate} به‌روزرسانی شد"
        except Exception as e:
            return f"خطا در به‌روزرسانی قیمت‌ها: {str(e)}"

    def __str__(self):
        return f"1 USD = {self.rate} Toman"


# ----------------------------
# Category
# ----------------------------
class Category(BaseModel):
    image = models.ImageField(upload_to=upload_to_category, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta(BaseModel.Meta):
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    @property
    def is_parent(self):
        return self.children.exists()

    @property
    def active_subcategories(self):
        return self.children.filter(isActive=True)

    def get_all_subcategories(self):
        subcategories = []
        for child in self.children.filter(isActive=True):
            subcategories.append(child)
            subcategories.extend(child.get_all_subcategories())
        return subcategories


# ----------------------------
# Restaurant
# ----------------------------
class Restaurant(BaseModel):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='restaurants', null=True, blank=True)
    english_name = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="نام انگلیسی برای تولید اسلاگ")
    description = models.TextField(null=True, blank=True, verbose_name="توضیح فارسی")
    description_en = models.TextField(null=True, blank=True, verbose_name="توضیح انگلیسی")
    logo = models.ImageField(upload_to=upload_to_restaurant_logo, null=True, blank=True)
    coverImage = models.ImageField(upload_to=upload_to_restaurant_cover, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    address_en = models.TextField(null=True, blank=True, verbose_name="آدرس انگلیسی")
    openingTime = models.TimeField(null=True, blank=True)
    closingTime = models.TimeField(null=True, blank=True)
    minimumOrder = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deliveryFee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taxRate = models.DecimalField(max_digits=5, decimal_places=2, default=9.0, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.english_name:
            base_slug = slugify(self.english_name)
            slug = base_slug
            counter = 1
            while Restaurant.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or self.title_en or self.english_name or "Restaurant"

    def get_address(self, lang='fa'):
        """دریافت آدرس بر اساس زبان"""
        if lang == 'en' and self.address_en:
            return self.address_en
        return self.address or self.address_en or ''


# ----------------------------
# Menu Category
# ----------------------------
class MenuCategory(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menuCategories', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    customTitle = models.CharField(max_length=255, null=True, blank=True, verbose_name="عنوان سفارشی فارسی")
    customTitle_en = models.CharField(max_length=255, null=True, blank=True, verbose_name="عنوان سفارشی انگلیسی")
    customImage = models.ImageField(upload_to=upload_to_menu_category, null=True, blank=True)
    displayOrder = models.IntegerField(default=0, null=True, blank=True)
    isActive = models.BooleanField(default=True, null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updatedAt = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['displayOrder']
        unique_together = ['restaurant', 'category']
        verbose_name = 'Menu Category'
        verbose_name_plural = 'Menu Categories'

    def __str__(self):
        title = self.customTitle or (self.category.title if self.category else "")
        return f"{self.restaurant.title if self.restaurant else 'No Restaurant'} - {title}"

    @property
    def displayImage(self):
        return self.customImage if self.customImage else self.category.image

    def get_title(self, lang='fa'):
        """دریافت عنوان بر اساس زبان"""
        if lang == 'en':
            if self.customTitle_en:
                return self.customTitle_en
            elif self.category and self.category.title_en:
                return self.category.title_en
        return self.customTitle or (self.category.title if self.category else "")


# ----------------------------
# Food
# ----------------------------
class Food(BaseModel):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='foods', null=True, blank=True)
    menuCategory = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='foods', null=True, blank=True)
    description = models.TextField(null=True, blank=True, verbose_name="توضیح فارسی")
    description_en = models.TextField(null=True, blank=True, verbose_name="توضیح انگلیسی")
    image = models.ImageField(upload_to=upload_to_food_image, null=True, blank=True)
    sound = models.FileField(upload_to=upload_to_food_sound, null=True, blank=True)
    price = models.PositiveIntegerField(null=True, blank=True, verbose_name="قیمت (تومان)")
    price_usd_cents = models.PositiveIntegerField(null=True, blank=True, verbose_name="قیمت (سنت)")
    preparationTime = models.IntegerField(help_text="زمان آماده‌سازی (دقیقه)", null=True, blank=True)

    class Meta:
        ordering = ['displayOrder']

    def save(self, *args, **kwargs):
        # محاسبه خودکار قیمت دلار اگر وجود ندارد
        if self.price and not self.price_usd_cents:
            self.update_usd_price()

        if not self.slug and self.title:
            base_slug = slugify(self.title_en or self.title)
            slug = base_slug
            counter = 1
            while Food.objects.filter(slug=slug, restaurant=self.restaurant).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def update_usd_price(self, exchange_rate=None):
        """بروزرسانی قیمت دلار بر اساس نرخ جدید"""
        if self.price:
            if exchange_rate is None:
                exchange_rate = get_current_exchange_rate()

            usd_amount = Decimal(self.price) / Decimal(exchange_rate)
            self.price_usd_cents = int(usd_amount * 100)

    @property
    def price_usd(self):
        """قیمت به دلار (عدد اعشاری)"""
        if self.price_usd_cents:
            return Decimal(self.price_usd_cents) / Decimal(100)
        return None

    @property
    def formatted_price_usd(self):
        """قیمت فرمت شده به دلار"""
        if self.price_usd:
            return f"${self.price_usd:.2f}"
        return None

    @property
    def current_exchange_rate(self):
        """نرخ ارز فعلی استفاده شده"""
        return get_current_exchange_rate()

    def get_price_display(self, lang='fa'):
        """نمایش قیمت بر اساس زبان"""
        if lang == 'en':
            return self.formatted_price_usd or f"${0:.2f}"
        else:
            from django.contrib.humanize.templatetags.humanize import intcomma
            return f"{intcomma(self.price or 0)} تومان"

    def __str__(self):
        return self.title or self.title_en or "Food"


# ----------------------------
# Helper functions
# ----------------------------
def update_all_food_prices():
    """به‌روزرسانی قیمت تمام غذاها بر اساس نرخ ارز فعلی"""
    try:
        current_rate = ExchangeRate.objects.filter(is_active=True).first()
        if current_rate:
            return current_rate.update_all_food_prices()
        return "No active exchange rate found"
    except Exception as e:
        return f"Error updating prices: {str(e)}"


def get_current_exchange_rate():
    """دریافت نرخ ارز فعلی"""
    try:
        current_rate = ExchangeRate.objects.filter(is_active=True).first()
        if current_rate:
            return current_rate.rate
    except:
        pass
    return getattr(settings, 'EXCHANGE_RATE', 60000)