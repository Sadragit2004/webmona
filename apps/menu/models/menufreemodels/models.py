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

    def get_title(self, lang):
        if lang == 'en':
            return self.title_en or self.title or ''
        return self.title or self.title_en or ''

    def get_description(self, lang='fa'):
        if hasattr(self, 'description') and hasattr(self, 'description_en'):
            if lang == 'en':
                return self.description_en or self.description or ''
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
        # ✅ جلوگیری از خطای رشته خالی در TimeField
        if self.openingTime == "":
            self.openingTime = None
        if self.closingTime == "":
            self.closingTime = None

        # ساخت اسلاگ بر اساس نام انگلیسی
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
        if lang == 'en':
            return self.address_en or self.address or ''
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
        return self.customImage if self.customImage else (self.category.image if self.category else None)

    def get_title(self, lang='fa'):
        title_fa = self.customTitle or (self.category.title if self.category else None)
        title_en = self.customTitle_en or (self.category.title_en if self.category else None)
        if lang == 'en':
            return title_en or title_fa or ""
        return title_fa or title_en or ""


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
        if self.price is not None and self.price_usd_cents is None:
            self.update_usd_price()

        if not self.slug and (self.title or self.title_en):
            base_slug = slugify(self.title_en or self.title)
            slug = base_slug
            counter = 1
            while Food.objects.filter(slug=slug, restaurant=self.restaurant).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def update_usd_price(self, exchange_rate=None):
        if self.price is not None:
            if exchange_rate is None:
                exchange_rate = get_current_exchange_rate()
            if exchange_rate and exchange_rate > 0:
                usd_amount = Decimal(self.price) / Decimal(exchange_rate)
                self.price_usd_cents = int(usd_amount * 100)
            else:
                self.price_usd_cents = 0
        else:
            self.price_usd_cents = None

    @property
    def price_usd(self):
        if self.price_usd_cents is not None:
            return Decimal(self.price_usd_cents) / Decimal(100)
        return None

    @property
    def formatted_price_usd(self):
        if self.price_usd is not None:
            return f"${self.price_usd:.2f}"
        return None

    @property
    def current_exchange_rate(self):
        return get_current_exchange_rate()

    def get_price_display(self, lang='fa'):
        if lang == 'en':
            if self.price_usd_cents:
                usd_amount = Decimal(self.price_usd_cents) / Decimal(100)
                return f"${usd_amount:.2f}"
            elif self.price:
                exchange_rate = get_current_exchange_rate()
                if exchange_rate:
                    usd_amount = Decimal(self.price) / Decimal(exchange_rate)
                    return f"${usd_amount:.2f}"
            return "$0.00"
        else:
            from django.contrib.humanize.templatetags.humanize import intcomma
            return f"{intcomma(self.price or 0)} تومان"

    def __str__(self):
        return self.title or self.title_en or "Food"


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
        if self.is_active:
            ExchangeRate.objects.filter(is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)
        if self.is_active:
            self.update_all_food_prices()

    def update_all_food_prices(self):
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
# Helper functions
# ----------------------------
def update_all_food_prices():
    try:
        current_rate = ExchangeRate.objects.filter(is_active=True).first()
        if current_rate:
            return current_rate.update_all_food_prices()
        return "No active exchange rate found"
    except Exception as e:
        return f"Error updating prices: {str(e)}"


def get_current_exchange_rate():
    try:
        current_rate = ExchangeRate.objects.filter(is_active=True).first()
        if current_rate:
            return current_rate.rate
    except:
        pass
    return getattr(settings, 'EXCHANGE_RATE', Decimal('60000.00'))
