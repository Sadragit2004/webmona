from django.contrib import admin
from .models import Product, ProductFeature, ProductGallery

class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1

class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active', 'publish_date']
    list_filter = ['is_active', 'publish_date']
    search_fields = ['name', 'description']
    inlines = [ProductFeatureInline, ProductGalleryInline]

@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = ['product', 'key', 'value', 'slug']
    list_filter = ['product']
    search_fields = ['key', 'value']

@admin.register(ProductGallery)
class ProductGalleryAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'is_active']
    list_filter = ['is_active', 'product']
    search_fields = ['alt_text']