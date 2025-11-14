from django.contrib import admin
from django.utils.html import format_html
from .models import Plan, PlanFeature

class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1
    fields = ['title', 'value', 'order', 'isAvailable']
    ordering = ['order']
    classes = ['collapse']

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'display_price',
        'expiryDays',
        'isActive',
        'createdAt',
        'feature_count'
    ]
    list_filter = ['isActive', 'createdAt', 'expiryDays']
    search_fields = ['name', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PlanFeatureInline]
    readonly_fields = ['createdAt', 'updatedAt']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'name',
                'slug',
                'description',
            )
        }),
        ('قیمت و اعتبار', {
            'fields': (
                'price',
                'expiryDays'
            )
        }),
        ('وضعیت و تاریخ‌ها', {
            'fields': (
                'isActive','isFavorit',
                ('createdAt', 'updatedAt')
            )
        }),
    )

    def display_price(self, obj):
        if obj.price:
            return f"{obj.price:,} تومان"
        return "رایگان"
    display_price.short_description = "قیمت"



    def feature_count(self, obj):
        return obj.features.count()
    feature_count.short_description = "تعداد ویژگی‌ها"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('features')

@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'value',

        'plan',
        'order',
        'isAvailable'
    ]
    list_filter = ['isAvailable', 'plan']
    search_fields = ['title', 'value', 'plan__name']
    list_editable = ['order', 'isAvailable']
    ordering = ['plan', 'order']
    fieldsets = (
        ('اطلاعات ویژگی', {
            'fields': (
                'plan',
                'title',
                'value'
            )
        }),
        ('تنظیمات نمایش', {
            'fields': (
                'order',
                'isAvailable',

            )
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('plan')


# apps/plan/admin.py
from django.contrib import admin
from .models import Plan, PlanFeature, PlanOrder

@admin.register(PlanOrder)
class PlanOrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'finalPrice', 'isPaid', 'createdAt', 'expiryDate', 'is_expired']
    list_filter = ['isPaid', 'createdAt', 'plan']
    search_fields = ['user__username', 'user__email', 'plan__name']
    readonly_fields = ['createdAt']

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'منقضی شده'