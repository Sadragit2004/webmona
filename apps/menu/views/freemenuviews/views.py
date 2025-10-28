from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.conf import settings
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from ...models.menufreemodels.models import Restaurant, MenuCategory, Food, Category, ExchangeRate

# در views.py - تابع digital_menu
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
        'lang': lang
    }

    # استفاده از تمپلیت انگلیسی برای زبان انگلیسی
    if lang == 'en':
        return render(request, 'menu_app/free/restaurant_en.html', context)
    else:
        return render(request, 'menu_app/free/restaurant.html', context)

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
            'price_display': food.get_price_display(lang),
            'preparationTime': food.preparationTime,
            'image': food.image.url if food.image else None,
            'sound': food.sound.url if food.sound else None,
            'category_id': food.menuCategory.id if food.menuCategory else None
        })

    return JsonResponse({'foods': foods_data})

def search_foods(request, restaurant_slug):
    """جستجوی غذاها (API)"""
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, isActive=True)
    query = request.GET.get('q', '').strip()
    lang = request.GET.get('lang', 'fa')

    if query:
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
            'price_display': food.get_price_display(lang),
            'preparationTime': food.preparationTime,
            'image': food.image.url if food.image else None,
            'sound': food.sound.url if food.sound else None,
            'category_id': food.menuCategory.id if food.menuCategory else None
        })

    return JsonResponse({'foods': foods_data})

def change_language(request, restaurant_slug):
    """تغییر زبان"""
    lang = request.GET.get('lang', 'fa')
    if lang not in ['fa', 'en']:
        lang = 'fa'

    # استفاده از reverse و اضافه کردن query parameter
    url = reverse('menu:digital_menu', kwargs={'restaurant_slug': restaurant_slug})
    return redirect(f"{url}?lang={lang}")