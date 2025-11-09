from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models.menufreemodels.models import Category, Restaurant, MenuCategory, Food, ExchangeRate
from .helper import update_all_food_prices


# ----------------------------
# Mixin for bilingual support
# ----------------------------
class BilingualAdminMixin:
    """میکسین برای پشتیبانی از نمایش دو زبانه در ادمین"""

    def get_title_display(self, obj):
        """نمایش عنوان دو زبانه"""
        title_fa = obj.title or '-'
        title_en = obj.title_en or '-'
        return format_html(
            '<div style="direction: rtl; text-align: right;">'
            '<strong>فارسی:</strong> {}<br>'
            '<strong>English:</strong> {}'
            '</div>',
            title_fa, title_en
        )
    get_title_display.short_description = _('Title')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin, BilingualAdminMixin):
    list_display = ['get_title_display', 'slug', 'isActive', 'displayOrder', 'createdAt', 'get_image_preview']
    list_filter = ['isActive', 'createdAt']
    search_fields = ['title', 'title_en', 'slug']
    readonly_fields = ['createdAt', 'updatedAt', 'get_image_preview', 'get_title_display']
    list_editable = ['isActive', 'displayOrder']
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('get_title_display', 'title', 'title_en', 'slug', 'isActive', 'displayOrder')
        }),
        (_('Relations'), {
            'fields': ('parent',)
        }),
        (_('Media'), {
            'fields': ('image', 'get_image_preview')
        }),
        (_('Timestamps'), {
            'fields': ('createdAt', 'updatedAt'),
            'classes': ('collapse',)
        }),
    )

    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.image.url)
        return _("No Image")
    get_image_preview.short_description = _('Image Preview')


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin, BilingualAdminMixin):
    list_display = ['get_title_display', 'slug', 'phone', 'isActive', 'displayOrder', 'createdAt', 'get_logo_preview']
    list_filter = ['isActive', 'createdAt']
    search_fields = ['title', 'title_en', 'slug', 'phone', 'address', 'address_en']
    readonly_fields = ['createdAt', 'updatedAt', 'get_logo_preview', 'get_cover_preview', 'get_title_display']
    list_editable = ['isActive', 'displayOrder']
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'owner', 'get_title_display', 'title', 'title_en', 'slug', 'text',
                'description', 'description_en',
                'isActive', 'displayOrder'
            )
        }),
        (_('Contact Information'), {
            'fields': ('phone', 'address', 'address_en')
        }),
        (_('Images'), {
            'fields': ('logo', 'get_logo_preview', 'coverImage', 'get_cover_preview')
        }),
        (_('Business Settings'), {
            'fields': ('openingTime', 'closingTime', 'minimumOrder', 'deliveryFee', 'taxRate')
        }),
        (_('Timestamps'), {
            'fields': ('createdAt', 'updatedAt'),
            'classes': ('collapse',)
        }),
    )

    def get_logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.logo.url)
        return _("No Logo")
    get_logo_preview.short_description = _('Logo Preview')

    def get_cover_preview(self, obj):
        if obj.coverImage:
            return format_html('<img src="{}" width="80" height="40" style="border-radius: 3px;" />', obj.coverImage.url)
        return _("No Cover")
    get_cover_preview.short_description = _('Cover Preview')


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'get_category_title', 'displayOrder', 'isActive', 'createdAt', 'get_image_preview']
    list_filter = ['isActive', 'restaurant', 'category', 'createdAt']
    search_fields = ['restaurant__title', 'restaurant__title_en', 'category__title', 'category__title_en', 'customTitle', 'customTitle_en']
    readonly_fields = ['createdAt', 'updatedAt', 'get_image_preview', 'get_title_display']
    list_editable = ['isActive', 'displayOrder']
    list_select_related = ['restaurant', 'category']

    def get_category_title(self, obj):
        if obj.customTitle or obj.customTitle_en:
            title_fa = obj.customTitle or '-'
            title_en = obj.customTitle_en or '-'
        else:
            title_fa = obj.category.title if obj.category else '-'
            title_en = obj.category.title_en if obj.category else '-'
        return format_html(
            '<div style="direction: rtl; text-align: right;">'
            '<strong>فارسی:</strong> {}<br>'
            '<strong>English:</strong> {}'
            '</div>',
            title_fa, title_en
        )
    get_category_title.short_description = _('Category Title')

    def get_title_display(self, obj):
        return self.get_category_title(obj)
    get_title_display.short_description = _('Title Display')

    def get_image_preview(self, obj):
        if obj.displayImage:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.displayImage.url)
        return _("No Image")
    get_image_preview.short_description = _('Image Preview')

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('restaurant', 'category', 'isActive', 'displayOrder')
        }),
        (_('Custom Titles'), {
            'fields': ('get_title_display', 'customTitle', 'customTitle_en'),
            'description': _('If you want to show different titles than the main category, enter them here')
        }),
        (_('Custom Image'), {
            'fields': ('customImage', 'get_image_preview'),
            'description': _('If you want to show a different image than the main category, upload here')
        }),
        (_('Timestamps'), {
            'fields': ('createdAt', 'updatedAt'),
            'classes': ('collapse',)
        }),
    )


# ----------------------------
# FOOD ADMIN (ویرایش‌شده برای ManyToMany)
# ----------------------------
@admin.register(Food)
class FoodAdmin(admin.ModelAdmin, BilingualAdminMixin):
    list_display = [
        'get_title_display', 'get_restaurants_list', 'menuCategory',
        'get_price_display', 'preparationTime', 'isActive', 'displayOrder', 'image_preview'
    ]
    list_filter = ['isActive', 'restaurants', 'menuCategory', 'createdAt']
    search_fields = [
        'title', 'title_en', 'description', 'description_en',
        'restaurants__title', 'restaurants__title_en'
    ]
    readonly_fields = [
        'createdAt', 'updatedAt', 'image_preview', 'sound_preview',
        'get_title_display', 'get_price_info'
    ]
    list_editable = ['preparationTime', 'isActive', 'displayOrder']
    prepopulated_fields = {"slug": ("title",)}
    list_select_related = ['menuCategory__category']

    # 🧩 نمایش لیست رستوران‌ها به صورت کاما جدا
    def get_restaurants_list(self, obj):
        return ", ".join([r.title for r in obj.restaurants.all()])
    get_restaurants_list.short_description = _('Restaurants')

    def get_price_display(self, obj):
        price_toman = f"{obj.price:,} تومان" if obj.price else _("Not set")
        price_usd = obj.formatted_price_usd or _("Not set")
        return format_html(
            '<div style="direction: rtl; text-align: right;">'
            '<strong>تومان:</strong> {}<br>'
            '<strong>USD:</strong> {}'
            '</div>',
            price_toman, price_usd
        )
    get_price_display.short_description = _('Price')

    def get_price_info(self, obj):
        exchange_rate = obj.current_exchange_rate
        return format_html(
            '<div style="direction: rtl; text-align: right; background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>نرخ ارز فعلی:</strong> {} تومان<br>'
            '<strong>قیمت تومان:</strong> {}<br>'
            '<strong>قیمت USD:</strong> {}<br>'
            '<strong>قیمت سنت:</strong> {}'
            '</div>',
            exchange_rate,
            f"{obj.price:,} تومان" if obj.price else _("Not set"),
            obj.formatted_price_usd or _("Not set"),
            f"{obj.price_usd_cents} cents" if obj.price_usd_cents else _("Not set")
        )
    get_price_info.short_description = _('Price Information')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.image.url)
        return _("No Image")
    image_preview.short_description = _('Image Preview')

    def sound_preview(self, obj):
        if obj.sound:
            return format_html(
                '<audio controls style="height: 30px; width: 200px;">'
                '<source src="{}" type="audio/mpeg">'
                '{}'
                '</audio>',
                obj.sound.url, _("Your browser does not support audio")
            )
        return _("No Sound")
    sound_preview.short_description = _('Sound Preview')

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'get_title_display', 'title', 'title_en', 'slug',
                'description', 'description_en',
                'restaurants', 'menuCategory'
            )
        }),
        (_('Pricing'), {
            'fields': ('price', 'get_price_info', 'price_usd_cents')
        }),
        (_('Time & Settings'), {
            'fields': ('preparationTime', 'isActive', 'displayOrder')
        }),
        (_('Media'), {
            'fields': ('image', 'image_preview', 'sound', 'sound_preview')
        }),
        (_('Timestamps'), {
            'fields': ('createdAt', 'updatedAt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['rate', 'is_active', 'created_at', 'get_food_count']
    list_editable = ['is_active']
    list_filter = ['is_active', 'created_at']

    def get_food_count(self, obj):
        count = Food.objects.filter(price__isnull=False).count()
        return f"{count} foods"
    get_food_count.short_description = _('Affected Foods')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_active:
            result = update_all_food_prices()
            messages.info(request, result)

    fieldsets = (
        (_('Exchange Rate Information'), {
            'fields': ('rate', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
