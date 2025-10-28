from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.conf import settings
from django.db.models import Q  # اضافه کردن این خط
from ...models.menufreemodels.models import Restaurant, MenuCategory, Food, Category, ExchangeRate

def digital_menu(request, restaurant_slug):
    """صفحه اصلی منوی دیجیتال"""
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, isActive=True)

    # تشخیص زبان از URL یا تنظیمات
    lang = request.GET.get('lang', 'fa')
    if lang not in ['fa', 'en']:
        lang = 'fa'

    # دریافت دسته‌بندی‌های فعال رستوران
    menu_categories = MenuCategory.objects.filter(
        restaurant=restaurant,
        isActive=True
    ).select_related('category').prefetch_related('foods')

    # دریافت همه غذاهای فعال رستوران
    foods = Food.objects.filter(
        restaurant=restaurant,
        isActive=True
    ).select_related('menuCategory__category')

    # دریافت نرخ ارز فعلی
    from ...models.menufreemodels.models import get_current_exchange_rate
    exchange_rate = get_current_exchange_rate()

    context = {
        'restaurant': restaurant,
        'menu_categories': menu_categories,
        'foods': foods,
        'current_language': lang,
        'exchange_rate': exchange_rate,
    }

    template = 'menu_app/free/restaurant_en.html' if lang == 'en' else 'menu_app/free/restaurant.html'
    return render(request, template, context)

def get_foods_by_category(request, restaurant_slug, category_id):
    """دریافت غذاها بر اساس دسته‌بندی (API)"""
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, isActive=True)
    lang = request.GET.get('lang', 'fa')

    if category_id == 'all':
        foods = Food.objects.filter(restaurant=restaurant, isActive=True)
    else:
        menu_category = get_object_or_404(MenuCategory, id=category_id, restaurant=restaurant, isActive=True)
        foods = Food.objects.filter(menuCategory=menu_category, isActive=True)

    foods_data = []
    for food in foods:
        foods_data.append({
            'id': food.id,
            'title': food.title_en if lang == 'en' and food.title_en else food.title,
            'description': food.description_en if lang == 'en' and food.description_en else food.description,
            'price': food.price,
            'price_usd': food.formatted_price_usd,
            'price_usd_cents': food.price_usd_cents,
            'preparationTime': food.preparationTime,
            'image': food.image.url if food.image else '/static/images/default-food.jpg',
            'sound': food.sound.url if food.sound else None,
            'category': food.menuCategory.category.title_en if lang == 'en' and food.menuCategory and food.menuCategory.category.title_en else (food.menuCategory.category.title if food.menuCategory else _('دسته‌بندی نشده'))
        })

    return JsonResponse({'foods': foods_data})

def search_foods(request, restaurant_slug):
    """جستجوی غذاها (API)"""
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, isActive=True)
    query = request.GET.get('q', '').strip()
    lang = request.GET.get('lang', 'fa')

    if query:
        # جستجو در هر دو زبان
        foods = Food.objects.filter(
            restaurant=restaurant,
            isActive=True
        ).filter(
            Q(title__icontains=query) |
            Q(title_en__icontains=query) |
            Q(description__icontains=query) |
            Q(description_en__icontains=query)
        )
    else:
        foods = Food.objects.filter(restaurant=restaurant, isActive=True)

    foods_data = []
    for food in foods:
        foods_data.append({
            'id': food.id,
            'title': food.title_en if lang == 'en' and food.title_en else food.title,
            'description': food.description_en if lang == 'en' and food.description_en else food.description,
            'price': food.price,
            'price_usd': food.formatted_price_usd,
            'price_usd_cents': food.price_usd_cents,
            'preparationTime': food.preparationTime,
            'image': food.image.url if food.image else '/static/images/default-food.jpg',
            'sound': food.sound.url if food.sound else None,
            'category': food.menuCategory.category.title_en if lang == 'en' and food.menuCategory and food.menuCategory.category.title_en else (food.menuCategory.category.title if food.menuCategory else _('دسته‌بندی نشده'))
        })

    return JsonResponse({'foods': foods_data})

def change_language(request, restaurant_slug):
    """تغییر زبان"""
    lang = request.GET.get('lang', 'fa')
    if lang not in ['fa', 'en']:
        lang = 'fa'

    return digital_menu(request, restaurant_slug)