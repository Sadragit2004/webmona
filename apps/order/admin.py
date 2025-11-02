from django.contrib import admin
from .models import Ordermenu, MenuImage


@admin.register(Ordermenu)
class OrdermenuAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'restaurant',
        'status',
        'isfinaly',
        'isActive',
        'get_status_display',
        'get_fixed_price',
    )
    list_filter = ('status', 'isfinaly', 'isActive', 'restaurant')
    search_fields = ('restaurant__name',)
    readonly_fields = ('get_fixed_price',)
    ordering = ('-id',)
    list_display_links = ('id', 'restaurant')

    fieldsets = (
        (None, {
            'fields': (
                'restaurant',
                'status',
                'isfinaly',
                'isActive',
                'image',
            )
        }),
        ('اطلاعات اضافی', {
            'fields': ('get_fixed_price',),
            'classes': ('collapse',)
        }),
    )

    def get_status_display(self, obj):
        """نمایش متن وضعیت به‌جای عدد"""
        return obj.get_status_display()
    get_status_display.short_description = "وضعیت"


@admin.register(MenuImage)
class MenuImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'created_at', 'preview_image')
    list_filter = ('created_at',)
    search_fields = ('order__id',)
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        """پیش‌نمایش عکس در پنل ادمین"""
        if obj.image:
            return f'<img src="{obj.image.url}" width="80" style="border-radius:8px;" />'
        return "بدون تصویر"
    preview_image.allow_tags = True
    preview_image.short_description = "پیش‌نمایش عکس"

