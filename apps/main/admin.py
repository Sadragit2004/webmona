from django.contrib import admin
from django.utils.html import format_html
from .models import TextImageBlock


@admin.register(TextImageBlock)
class TextImageBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "image_position", "order")
    search_fields = ("title", "text",)