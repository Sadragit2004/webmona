from django.contrib import admin,messages
from django.utils.html import format_html
from .models.menufreemodels.models import Category, Restaurant, MenuCategory, Food,ExchangeRate


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'isActive', 'displayOrder', 'createdAt', 'get_image_preview']
    list_filter = ['isActive', 'createdAt']
    search_fields = ['title', 'slug']
    readonly_fields = ['createdAt', 'updatedAt', 'get_image_preview']
    list_editable = ['isActive', 'displayOrder']
    prepopulated_fields = {"slug": ("title",)}

    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    get_image_preview.short_description = 'Image Preview'


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'phone', 'isActive', 'displayOrder', 'createdAt', 'get_logo_preview']
    list_filter = ['isActive', 'createdAt']
    search_fields = ['title', 'slug', 'phone', 'address']
    readonly_fields = ['createdAt', 'updatedAt', 'get_logo_preview', 'get_cover_preview']
    list_editable = ['isActive', 'displayOrder']
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        ('Basic Information', {
            'fields': ('owner','title', 'slug', 'description', 'isActive', 'displayOrder')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address')
        }),
        ('Images', {
            'fields': ('logo', 'get_logo_preview', 'coverImage', 'get_cover_preview')
        }),
        ('Business Settings', {
            'fields': ('openingTime', 'closingTime', 'minimumOrder', 'deliveryFee', 'taxRate')
        }),
        ('Timestamps', {
            'fields': ('createdAt', 'updatedAt'),
            'classes': ('collapse',)
        }),
    )

    def get_logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "-"
    get_logo_preview.short_description = 'Logo Preview'

    def get_cover_preview(self, obj):
        if obj.coverImage:
            return format_html('<img src="{}" width="80" height="40" />', obj.coverImage.url)
        return "-"
    get_cover_preview.short_description = 'Cover Preview'


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'category', 'displayOrder', 'isActive', 'createdAt', 'get_image_preview']
    list_filter = ['isActive', 'restaurant', 'category', 'createdAt']
    search_fields = ['restaurant__title', 'category__title']
    readonly_fields = ['createdAt', 'updatedAt', 'get_image_preview']
    list_editable = ['isActive', 'displayOrder']
    list_select_related = ['restaurant', 'category']

    def get_image_preview(self, obj):
        if obj.displayImage:
            return format_html('<img src="{}" width="50" height="50" />', obj.displayImage.url)
        return "-"
    get_image_preview.short_description = 'Image Preview'

    fieldsets = (
        ('Basic Information', {
            'fields': ('restaurant', 'category', 'isActive', 'displayOrder')
        }),
        ('Custom Image', {
            'fields': ('customImage', 'get_image_preview'),
            'description': 'اگر می‌خواهید تصویر متفاوتی از دسته‌بندی اصلی نمایش داده شود، اینجا آپلود کنید'
        }),
        ('Timestamps', {
            'fields': ('createdAt', 'updatedAt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ['title', 'restaurant', 'menuCategory', 'price', 'preparationTime', 'isActive', 'displayOrder', 'image_preview']
    list_filter = ['isActive', 'restaurant', 'menuCategory', 'createdAt']
    search_fields = ['title', 'description', 'restaurant__title', 'menuCategory__category__title']
    readonly_fields = ['createdAt', 'updatedAt', 'image_preview', 'sound_preview']
    list_editable = ['price', 'preparationTime', 'isActive', 'displayOrder']
    prepopulated_fields = {"slug": ("title",)}
    list_select_related = ['restaurant', 'menuCategory__category']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image Preview'

    def sound_preview(self, obj):
        if obj.sound:
            return format_html(
                '<audio controls style="height: 30px;"><source src="{}" type="audio/mpeg">مرورگر شما از پخش صدا پشتیبانی نمی‌کند</audio>',
                obj.sound.url
            )
        return "-"
    sound_preview.short_description = 'Sound Preview'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'restaurant', 'menuCategory')
        }),
        ('Pricing & Time', {
            'fields': ('price', 'preparationTime')
        }),
        ('Media', {
            'fields': ('image', 'image_preview', 'sound', 'sound_preview')
        }),
        ('Settings', {
            'fields': ('isActive', 'displayOrder')
        }),
        ('Timestamps', {
            'fields': ('createdAt', 'updatedAt'),
            'classes': ('collapse',)
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # فیلتر کردن menuCategory بر اساس restaurant انتخاب شده
        if db_field.name == "menuCategory":
            if 'restaurant' in request.GET:
                kwargs["queryset"] = MenuCategory.objects.filter(restaurant_id=request.GET['restaurant'])
            elif hasattr(request, '_obj') and request._obj and request._obj.restaurant:
                kwargs["queryset"] = MenuCategory.objects.filter(restaurant=request._obj.restaurant)
            else:
                kwargs["queryset"] = MenuCategory.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_changeform_initial_data(self, request):
        # تنظیم مقدار اولیه برای restaurant اگر از طریق پارامتر آمده باشد
        initial = super().get_changeform_initial_data(request)
        if 'restaurant' in request.GET:
            initial['restaurant'] = request.GET['restaurant']
        return initial

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # ذخیره object برای استفاده در formfield_for_foreignkey
        try:
            obj = self.model.objects.get(pk=object_id)
            request._obj = obj
        except self.model.DoesNotExist:
            pass
        return super().change_view(request, object_id, form_url, extra_context)




# admin.py
@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['rate', 'is_active', 'created_at']
    list_editable = ['is_active']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # به‌روزرسانی خودکار قیمت تمام غذاها پس از تغییر نرخ ارز
        if obj.is_active:
            from .models import update_all_food_prices
            result = update_all_food_prices()
            messages.info(request, result)