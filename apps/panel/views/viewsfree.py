# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json
from apps.menu.models.menufreemodels.models import Restaurant, Category, MenuCategory, Food

# دکوراتور برای بررسی مالکیت رستوران
def restaurant_owner_required(view_func):
    def wrapper(request, slug, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account:login')

        restaurant = get_object_or_404(Restaurant, slug=slug, isActive=True)

        # بررسی مالکیت
        if restaurant.owner != request.user:
            return HttpResponseForbidden("شما دسترسی به این رستوران را ندارید")

        request.restaurant = restaurant
        return view_func(request, slug, *args, **kwargs)
    return wrapper

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta
from apps.menu.models.menufreemodels.models import Restaurant
from apps.order.models import Ordermenu, MenuImage

@login_required
def panel(request):
    """پنل اصلی - نمایش رستوران‌های کاربر و سفارشات"""
    user_restaurants = Restaurant.objects.filter(owner=request.user, isActive=True)

    # دریافت سفارشات کاربر
    user_orders = Ordermenu.objects.filter(restaurant__owner=request.user)

    # سفارشات پرداخت شده
    paid_orders = user_orders.filter(status=Ordermenu.STATUS_PAID)

    # سفارشات تایید شده
    confirmed_orders = user_orders.filter(status=Ordermenu.STATUS_CONFIRMED)

    # سفارشات تحویل شده
    delivered_orders = user_orders.filter(status=Ordermenu.STATUS_DELIVERED)

    # سفارشات پرداخت نشده
    unpaid_orders = user_orders.filter(status=Ordermenu.STATUS_UNPAID)

    # آمار کلی
    today = timezone.now().date()

    # آمار سفارشات امروز - استفاده از created_at
    today_orders_count = user_orders.filter(
        created_at__date=today
    ).count()

    # آمار سفارشات این ماه
    month_start = today.replace(day=1)
    monthly_orders_count = user_orders.filter(
        created_at__date__gte=month_start
    ).count()

    # محاسبه درآمد
    today_revenue = paid_orders.filter(
        created_at__date=today
    ).count() * 99000  # هر سفارش 99,000 تومان

    monthly_revenue = paid_orders.filter(
        created_at__date__gte=month_start
    ).count() * 99000

    context = {
        'restaurants': user_restaurants,
        'has_restaurant': user_restaurants.exists(),

        # سفارشات
        'user_orders': user_orders,
        'paid_orders': paid_orders,
        'confirmed_orders': confirmed_orders,
        'delivered_orders': delivered_orders,
        'unpaid_orders': unpaid_orders,

        # آمار
        'today_orders': today_orders_count,
        'monthly_orders': monthly_orders_count,
        'today_revenue': today_revenue,
        'monthly_revenue': monthly_revenue,
        'purchased_menus': paid_orders.count(),

        # آمار نمونه (می‌تونی با داده‌های واقعی جایگزین کنی)
        'today_views': 150,
        'average_rating': 4.5,
    }

    return render(request, 'panel_app/free/panel.html', context)

@login_required
def order_detail(request, order_id):
    """جزئیات سفارش"""
    order = get_object_or_404(Ordermenu, id=order_id, restaurant__owner=request.user)

    # دریافت عکس‌های مربوط به سفارش
    menu_images = order.images.all()

    context = {
        'order': order,
        'menu_images': menu_images,
    }

    return render(request, 'panel_app/free/order_detail.html', context)

@login_required
def update_order_status(request, order_id):
    """به‌روزرسانی وضعیت سفارش"""
    if request.method == 'POST':
        order = get_object_or_404(Ordermenu, id=order_id, restaurant__owner=request.user)

        try:
            new_status = int(request.POST.get('status'))

            # بررسی معتبر بودن وضعیت
            valid_statuses = [status[0] for status in Ordermenu.STATUS_CHOICES]
            if new_status in valid_statuses:
                order.status = new_status
                order.save()

                return JsonResponse({
                    'success': True,
                    'message': 'وضعیت سفارش با موفقیت به‌روزرسانی شد',
                    'new_status': order.get_status_display()
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'وضعیت نامعتبر'
                })

        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'خطا در پردازش درخواست'
            })

    return JsonResponse({
        'success': False,
        'message': 'متد نامعتبر'
    })

@login_required
def process_payment(request, order_id):
    """پردازش پرداخت برای سفارشات پرداخت نشده"""
    order = get_object_or_404(Ordermenu, id=order_id, restaurant__owner=request.user)

    # فقط برای سفارشات پرداخت نشده
    if order.status != Ordermenu.STATUS_UNPAID:
        return JsonResponse({
            'success': False,
            'message': 'این سفارش قبلاً پرداخت شده است'
        })

    if request.method == 'POST':
        try:
            # در اینجا منطق پرداخت رو پیاده‌سازی کن
            # برای نمونه، وضعیت رو به پرداخت شده تغییر می‌دیم

            order.status = Ordermenu.STATUS_PAID
            order.isfinaly = True
            order.isActive = True
            order.save()

            return JsonResponse({
                'success': True,
                'message': 'پرداخت با موفقیت انجام شد',
                'redirect_url': f'/panel/orders/{order.id}/'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در پردازش پرداخت: {str(e)}'
            })

    # نمایش صفحه پرداخت
    context = {
        'order': order,
        'amount': order.get_fixed_price(),  # 99,000 تومان
    }

    return render(request, 'panel_app/free/payment_page.html', context)

@login_required
def cancel_order(request, order_id):
    """لغو سفارش"""
    if request.method == 'POST':
        order = get_object_or_404(Ordermenu, id=order_id, restaurant__owner=request.user)

        # فقط سفارشات پرداخت نشده قابل لغو هستند
        if order.status != Ordermenu.STATUS_UNPAID:
            return JsonResponse({
                'success': False,
                'message': 'فقط سفارشات پرداخت نشده قابل لغو هستند'
            })

        try:
            # حذف سفارش
            order.delete()

            return JsonResponse({
                'success': True,
                'message': 'سفارش با موفقیت لغو شد'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در لغو سفارش: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'متد نامعتبر'
    })

@login_required
def order_list(request):
    """لیست تمام سفارشات کاربر"""
    status_filter = request.GET.get('status', 'all')

    user_orders = Ordermenu.objects.filter(restaurant__owner=request.user)

    # فیلتر بر اساس وضعیت
    if status_filter == 'unpaid':
        orders = user_orders.filter(status=Ordermenu.STATUS_UNPAID)
    elif status_filter == 'paid':
        orders = user_orders.filter(status=Ordermenu.STATUS_PAID)
    elif status_filter == 'confirmed':
        orders = user_orders.filter(status=Ordermenu.STATUS_CONFIRMED)
    elif status_filter == 'delivered':
        orders = user_orders.filter(status=Ordermenu.STATUS_DELIVERED)
    else:
        orders = user_orders

    context = {
        'orders': orders.order_by('-id'),
        'current_filter': status_filter,
        'status_choices': Ordermenu.STATUS_CHOICES,
    }

    return render(request, 'panel_app/free/order_list.html', context)


@login_required
def create_restaurant(request):
    """ایجاد رستوران جدید"""
    if request.method == 'POST':
        try:
            data = request.POST
            files = request.FILES

            # بررسی نام انگلیسی تکراری
            english_name = data.get('english_name')
            if Restaurant.objects.filter(english_name=english_name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'این نام انگلیسی قبلاً انتخاب شده است'
                })

            # ایجاد رستوران جدید
            restaurant = Restaurant(
                owner=request.user,
                title=data.get('title'),
                english_name=english_name,
                description=data.get('description', ''),
                phone=data.get('phone', ''),
                address=data.get('address', ''),
                openingTime=data.get('opening_time'),
                closingTime=data.get('closing_time'),
                minimumOrder=data.get('minimum_order', 0),
                deliveryFee=data.get('delivery_fee', 0),
                taxRate=data.get('tax_rate', 9.0),
                isActive=True
            )

            # ذخیره لوگو
            if 'logo' in files:
                restaurant.logo = files['logo']

            # ذخیره تصویر کاور
            if 'cover_image' in files:
                restaurant.coverImage = files['cover_image']

            restaurant.save()

            return JsonResponse({
                'success': True,
                'message': 'رستوران با موفقیت ایجاد شد',
                'restaurant_slug': restaurant.slug
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در ایجاد رستوران: {str(e)}'
            })

    return render(request, 'panel_app/free/create_restaurant.html')



@login_required
@restaurant_owner_required
def restaurant_admin(request, slug):
    """پنل مدیریت منوی رستوران"""
    restaurant = request.restaurant

    # دریافت دسته‌بندی‌های رستوران (همه، نه فقط فعال)
    menu_categories = MenuCategory.objects.filter(
        restaurant=restaurant
    ).select_related('category').order_by('displayOrder')

    # دریافت همه دسته‌بندی‌های موجود برای افزودن به منو
    all_categories = Category.objects.filter(isActive=True).exclude(
        id__in=menu_categories.values_list('category_id', flat=True)
    )

    # دریافت غذاهای رستوران
    foods = Food.objects.filter(
        restaurant=restaurant
    ).select_related('menuCategory__category').order_by('displayOrder')

    context = {
        'restaurant': restaurant,
        'menu_categories': menu_categories,
        'all_categories': all_categories,
        'foods': foods,
        'categories': Category.objects.filter(isActive=True)
    }
    return render(request, 'panel_app/free/restaurant_admin.html', context)

@login_required
@restaurant_owner_required
@csrf_exempt
@require_http_methods(["POST"])
def add_food(request, slug):
    """افزودن غذای جدید"""
    restaurant = request.restaurant

    try:
        data = request.POST
        files = request.FILES

        # ایجاد غذای جدید
        food = Food(
            restaurant=restaurant,
            title=data.get('title'),
            description=data.get('description', ''),
            price=data.get('price', 0),
            preparationTime=data.get('preparation_time', 0),
            isActive=data.get('is_active', 'true').lower() == 'true'
        )

        # تنظیم دسته‌بندی منو
        menu_category_id = data.get('menu_category')
        if menu_category_id:
            menu_category = get_object_or_404(MenuCategory, id=menu_category_id, restaurant=restaurant)
            food.menuCategory = menu_category

        # ذخیره تصویر
        if 'image' in files:
            food.image = files['image']

        # ذخیره فایل صوتی
        if 'sound' in files:
            food.sound = files['sound']

        food.save()

        return JsonResponse({
            'success': True,
            'message': 'غذا با موفقیت اضافه شد',
            'food_id': food.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در افزودن غذا: {str(e)}'
        })

@login_required
@restaurant_owner_required
@csrf_exempt
@require_http_methods(["POST"])
def update_food(request, slug, food_id):
    """ویرایش غذا"""
    restaurant = request.restaurant
    food = get_object_or_404(Food, id=food_id, restaurant=restaurant)

    try:
        data = request.POST
        files = request.FILES

        # به‌روزرسانی فیلدها
        food.title = data.get('title', food.title)
        food.description = data.get('description', food.description)
        food.price = data.get('price', food.price)
        food.preparationTime = data.get('preparation_time', food.preparationTime)
        food.isActive = data.get('is_active', 'true').lower() == 'true'

        # به‌روزرسانی دسته‌بندی منو
        menu_category_id = data.get('menu_category')
        if menu_category_id:
            menu_category = get_object_or_404(MenuCategory, id=menu_category_id, restaurant=restaurant)
            food.menuCategory = menu_category
        else:
            food.menuCategory = None

        # به‌روزرسانی تصویر
        if 'image' in files:
            food.image = files['image']

        # به‌روزرسانی فایل صوتی
        if 'sound' in files:
            food.sound = files['sound']

        food.save()

        return JsonResponse({
            'success': True,
            'message': 'غذا با موفقیت ویرایش شد'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در ویرایش غذا: {str(e)}'
        })

@login_required
@restaurant_owner_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_food(request, slug, food_id):
    """حذف غذا"""
    restaurant = request.restaurant
    food = get_object_or_404(Food, id=food_id, restaurant=restaurant)

    try:
        food.delete()
        return JsonResponse({
            'success': True,
            'message': 'غذا با موفقیت حذف شد'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در حذف غذا: {str(e)}'
        })

@login_required
@restaurant_owner_required
@csrf_exempt
@require_http_methods(["POST"])
def toggle_food_status(request, slug, food_id):
    """تغییر وضعیت فعال/غیرفعال غذا"""
    restaurant = request.restaurant
    food = get_object_or_404(Food, id=food_id, restaurant=restaurant)

    try:
        food.isActive = not food.isActive
        food.save()

        status = "فعال" if food.isActive else "غیرفعال"
        return JsonResponse({
            'success': True,
            'message': f'وضعیت غذا به {status} تغییر کرد',
            'is_active': food.isActive
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در تغییر وضعیت: {str(e)}'
        })

@login_required
@restaurant_owner_required
@csrf_exempt
@require_http_methods(["POST"])
def add_menu_category(request, slug):
    """افزودن دسته‌بندی جدید به منوی رستوران"""
    restaurant = request.restaurant

    try:
        data = request.POST
        files = request.FILES

        category_id = data.get('category_id')
        if not category_id:
            return JsonResponse({
                'success': False,
                'message': 'لطفاً یک دسته‌بندی انتخاب کنید'
            })

        # بررسی وجود دسته‌بندی
        category = get_object_or_404(Category, id=category_id, isActive=True)

        # بررسی تکراری نبودن
        if MenuCategory.objects.filter(restaurant=restaurant, category=category).exists():
            return JsonResponse({
                'success': False,
                'message': 'این دسته‌بندی قبلاً به منو اضافه شده است'
            })

        # ایجاد دسته‌بندی منو
        menu_category = MenuCategory(
            restaurant=restaurant,
            category=category,
            isActive=data.get('is_active', 'true').lower() == 'true'
        )

        # ذخیره تصویر سفارشی
        if 'custom_image' in files:
            menu_category.customImage = files['custom_image']

        menu_category.save()

        return JsonResponse({
            'success': True,
            'message': 'دسته‌بندی با موفقیت به منو اضافه شد',
            'menu_category_id': menu_category.id,
            'category_title': category.title,
            'category_id': category.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در افزودن دسته‌بندی: {str(e)}'
        })

@login_required
@restaurant_owner_required
@csrf_exempt
@require_http_methods(["POST"])
def toggle_menu_category_status(request, slug, menu_category_id):
    """تغییر وضعیت فعال/غیرفعال دسته‌بندی"""
    restaurant = request.restaurant
    menu_category = get_object_or_404(MenuCategory, id=menu_category_id, restaurant=restaurant)

    try:
        menu_category.isActive = not menu_category.isActive
        menu_category.save()

        status = "فعال" if menu_category.isActive else "غیرفعال"
        return JsonResponse({
            'success': True,
            'message': f'وضعیت دسته‌بندی به {status} تغییر کرد',
            'is_active': menu_category.isActive
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در تغییر وضعیت: {str(e)}'
        })

@login_required
@restaurant_owner_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_menu_category(request, slug, menu_category_id):
    """حذف دسته‌بندی از منو"""
    restaurant = request.restaurant
    menu_category = get_object_or_404(MenuCategory, id=menu_category_id, restaurant=restaurant)

    try:
        # بررسی آیا غذاهایی در این دسته‌بندی وجود دارند
        if menu_category.foods.exists():
            return JsonResponse({
                'success': False,
                'message': 'امکان حذف دسته‌بندی وجود ندارد. ابتدا غذاهای این دسته‌بندی را حذف یا انتقال دهید.'
            })

        # حذف دسته‌بندی منو
        menu_category.delete()

        return JsonResponse({
            'success': True,
            'message': 'دسته‌بندی با موفقیت از منو حذف شد'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در حذف دسته‌بندی: {str(e)}'
        })

@login_required
@restaurant_owner_required
@csrf_exempt
@require_http_methods(["POST"])
def update_restaurant_settings(request, slug):
    """به‌روزرسانی تنظیمات رستوران"""
    restaurant = request.restaurant

    try:
        data = request.POST
        files = request.FILES

        # بررسی نام انگلیسی تکراری
        english_name = data.get('english_name')
        if english_name and english_name != restaurant.english_name:
            if Restaurant.objects.filter(english_name=english_name).exclude(id=restaurant.id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'این نام انگلیسی قبلاً انتخاب شده است'
                })

        # به‌روزرسانی فیلدها
        restaurant.title = data.get('title', restaurant.title)
        restaurant.english_name = english_name or restaurant.english_name
        restaurant.description = data.get('description', restaurant.description)
        restaurant.phone = data.get('phone', restaurant.phone)
        restaurant.address = data.get('address', restaurant.address)
        restaurant.openingTime = data.get('opening_time', restaurant.openingTime)
        restaurant.closingTime = data.get('closing_time', restaurant.closingTime)
        restaurant.minimumOrder = data.get('minimum_order', restaurant.minimumOrder)
        restaurant.deliveryFee = data.get('delivery_fee', restaurant.deliveryFee)
        restaurant.taxRate = data.get('tax_rate', restaurant.taxRate)

        # به‌روزرسانی لوگو
        if 'logo' in files:
            restaurant.logo = files['logo']

        # به‌روزرسانی تصویر کاور
        if 'cover_image' in files:
            restaurant.coverImage = files['cover_image']

        restaurant.save()

        return JsonResponse({
            'success': True,
            'message': 'تنظیمات رستوران با موفقیت به‌روزرسانی شد'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در به‌روزرسانی تنظیمات: {str(e)}'
        })

@login_required
@restaurant_owner_required
def get_foods_by_category(request, slug, category_id=None):
    """دریافت غذاها بر اساس دسته‌بندی"""
    restaurant = request.restaurant

    foods = Food.objects.filter(restaurant=restaurant)

    if category_id and category_id != 'all':
        foods = foods.filter(menuCategory__category__id=category_id)

    foods_data = []
    for food in foods:
        foods_data.append({
            'id': food.id,
            'title': food.title,
            'description': food.description,
            'price': food.price,
            'preparation_time': food.preparationTime,
            'image_url': food.image.url if food.image else '',
            'category_name': food.menuCategory.category.title if food.menuCategory and food.menuCategory.category else 'بدون دسته',
            'category_id': food.menuCategory.category.id if food.menuCategory and food.menuCategory.category else None,
            'is_active': food.isActive
        })

    return JsonResponse({
        'success': True,
        'foods': foods_data
    })

@login_required
@restaurant_owner_required
@csrf_exempt
@require_http_methods(["POST"])
def update_food_order(request, slug):
    """به‌روزرسانی ترتیب نمایش غذاها"""
    restaurant = request.restaurant

    try:
        data = json.loads(request.body)
        order_data = data.get('order', [])

        for item in order_data:
            food = get_object_or_404(Food, id=item['id'], restaurant=restaurant)
            food.displayOrder = item['order']
            food.save()

        return JsonResponse({
            'success': True,
            'message': 'ترتیب نمایش با موفقیت به‌روزرسانی شد'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در به‌روزرسانی ترتیب: {str(e)}'
        })

# Context Processor
def restaurant_context(request):
    """Context processor برای دسترسی به رستوران‌های کاربر در همه تمپلیت‌ها"""
    context = {}

    if request.user.is_authenticated:
        # دریافت رستوران‌های کاربر
        user_restaurants = Restaurant.objects.filter(owner=request.user, isActive=True)
        context['user_restaurants'] = user_restaurants

        # اگر در session رستوران جاری ذخیره شده
        current_restaurant_slug = request.session.get('current_restaurant_slug')
        if current_restaurant_slug:
            try:
                current_restaurant = Restaurant.objects.get(
                    slug=current_restaurant_slug,
                    owner=request.user,
                    isActive=True
                )
                context['current_restaurant'] = current_restaurant
                context['current_restaurant_slug'] = current_restaurant_slug
            except Restaurant.DoesNotExist:
                if 'current_restaurant_slug' in request.session:
                    del request.session['current_restaurant_slug']

    return context



# views.py - فقط توسعه ویو create_restaurant_modal
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_restaurant_modal(request):
    """مدیریت افتتاح رستوران از طریق مودال - نسخه اصلاح شده"""
    try:
        # بررسی نوع درخواست (JSON یا FormData)
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            files = None
        else:
            data = request.POST
            files = request.FILES

        step = data.get('step')
        menu_creation_type = data.get('menu_creation_type')

        # مرحله 1: دریافت نام و نام خانوادگی و نام رستوران
        if step == 1:
            name = data.get('name', '').strip()
            family = data.get('family', '').strip()
            restaurant_name = data.get('restaurant_name', '').strip()

            # اعتبارسنجی
            if not name or not family or not restaurant_name:
                return JsonResponse({
                    'success': False,
                    'message': 'لطفاً تمام فیلدها را پر کنید'
                })

            # ذخیره در session
            request.session['restaurant_data'] = {
                'step1': {
                    'name': name,
                    'family': family,
                    'restaurant_name': restaurant_name
                }
            }
            request.session.modified = True

            return JsonResponse({
                'success': True,
                'message': 'اطلاعات با موفقیت ذخیره شد',
                'next_step': 2
            })

        # مرحله 2: دریافت نام انگلیسی
        elif step == 2:
            english_name = data.get('english_name', '').strip().lower()

            if not english_name:
                return JsonResponse({
                    'success': False,
                    'message': 'لطفاً نام انگلیسی را وارد کنید'
                })

            # بررسی تکراری نبودن
            if Restaurant.objects.filter(english_name=english_name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'این نام انگلیسی قبلاً انتخاب شده است'
                })

            # ذخیره در session
            restaurant_data = request.session.get('restaurant_data', {})
            restaurant_data['step2'] = {'english_name': english_name}
            request.session['restaurant_data'] = restaurant_data
            request.session.modified = True

            return JsonResponse({
                'success': True,
                'message': 'نام انگلیسی تأیید شد',
                'next_step': 3
            })

        # مرحله 3: ایجاد رستوران (ساخت توسط خود کاربر)
        elif step == 3:
            # دریافت مستقیم داده‌ها
            name = data.get('name', '').strip()
            family = data.get('family', '').strip()
            restaurant_name = data.get('restaurant_name', '').strip()
            english_name = data.get('english_name', '').strip().lower()
            is_seo_enabled = data.get('is_seo_enabled', False)

            # اعتبارسنجی نهایی
            if not name or not family or not restaurant_name or not english_name:
                return JsonResponse({
                    'success': False,
                    'message': 'اطلاعات ناقص است. لطفاً از ابتدا شروع کنید'
                })

            # بررسی نهایی تکراری نبودن نام انگلیسی
            if Restaurant.objects.filter(english_name=english_name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'این نام انگلیسی قبلاً انتخاب شده است'
                })

            # به‌روزرسانی نام و نام خانوادگی کاربر
            request.user.name = name
            request.user.family = family
            request.user.save()

            # ایجاد رستوران
            restaurant = Restaurant(
                owner=request.user,
                title=restaurant_name,
                english_name=english_name,
                isActive=True
            )
            restaurant.save()

            # پاک کردن session
            if 'restaurant_data' in request.session:
                del request.session['restaurant_data']

            return JsonResponse({
                'success': True,
                'message': 'رستوران با موفقیت ایجاد شد',
                'redirect_url': f'/panel/{restaurant.slug}/admin/'
            })

        # مرحله جدید: ایجاد با شرکت (آپلود عکس‌ها)
        elif step == 'create_with_company':
            # دریافت داده‌ها
            name = data.get('name', '').strip()
            family = data.get('family', '').strip()
            restaurant_name = data.get('restaurant_name', '').strip()
            english_name = data.get('english_name', '').strip().lower()

            # دریافت وضعیت سئو و تبدیل به boolean
            is_seo_enabled_str = data.get('is_seo_enabled', '0')
            is_seo_enabled = is_seo_enabled_str == '1'

            # اعتبارسنجی
            if not name or not family or not restaurant_name or not english_name:
                return JsonResponse({
                    'success': False,
                    'message': 'اطلاعات ناقص است'
                })

            # بررسی تکراری نبودن نام انگلیسی
            if Restaurant.objects.filter(english_name=english_name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'این نام انگلیسی قبلاً انتخاب شده است'
                })

            # اگر فقط ذخیره عکس‌ها باشد (بدون پرداخت)
            if menu_creation_type == 'company_save_only':
                # ذخیره اطلاعات در session برای استفاده بعدی
                request.session['pending_restaurant'] = {
                    'name': name,
                    'family': family,
                    'restaurant_name': restaurant_name,
                    'english_name': english_name,
                    'is_seo_enabled': is_seo_enabled,
                    'menu_images_count': 0
                }

                # ذخیره عکس‌ها در session به صورت موقت
                menu_images = files.getlist('menu_images') if files else []
                saved_images_count = 0

                # ذخیره اطلاعات عکس‌ها در session (فقط نام و سایز)
                image_info_list = []
                for image in menu_images:
                    if saved_images_count < 10:  # حداکثر 10 عکس
                        image_info_list.append({
                            'name': image.name,
                            'size': image.size,
                            'type': image.content_type
                        })
                        saved_images_count += 1

                request.session['pending_restaurant']['menu_images_info'] = image_info_list
                request.session['pending_restaurant']['menu_images_count'] = saved_images_count
                request.session.modified = True

                # به‌روزرسانی نام کاربر
                request.user.name = name
                request.user.family = family
                request.user.save()

                return JsonResponse({
                    'success': True,
                    'message': f'عکس‌ها با موفقیت ذخیره شد ({saved_images_count} عکس)',
                    'saved_images': saved_images_count
                })

            # اگر پرداخت باشد
            else:
                # ایجاد رستوران
                restaurant = Restaurant(
                    owner=request.user,
                    title=restaurant_name,
                    english_name=english_name,
                    isActive=True
                )
                restaurant.save()

                # ایجاد سفارش برای پرداخت
                from apps.order.models import Ordermenu, MenuImage
                order = Ordermenu.objects.create(
                    restaurant=restaurant,
                    isfinaly=False,
                    isActive=False,
                    status=Ordermenu.STATUS_UNPAID,
                    is_seo_enabled=is_seo_enabled
                )

                # ذخیره عکس‌ها
                menu_images = files.getlist('menu_images') if files else []
                saved_images_count = 0

                for image in menu_images:
                    if saved_images_count < 10:  # حداکثر 10 عکس
                        MenuImage.objects.create(
                            order=order,
                            image=image
                        )
                        saved_images_count += 1

                # پاک کردن session
                if 'pending_restaurant' in request.session:
                    del request.session['pending_restaurant']

                return JsonResponse({
                    'success': True,
                    'message': f'رستوران ایجاد شد و {saved_images_count} عکس آپلود شد',
                    'order_id': order.id,
                    'redirect_url': f'/peyment/request/{order.id}/'
                })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در پردازش: {str(e)}'
        })


@login_required
def check_english_name(request):
    """بررسی تکراری نبودن نام انگلیسی"""
    english_name = request.GET.get('english_name', '').strip().lower()

    if not english_name:
        return JsonResponse({'available': False, 'message': 'نام انگلیسی نمی‌تواند خالی باشد'})

    # بررسی وجود نام انگلیسی
    exists = Restaurant.objects.filter(english_name=english_name).exists()

    if exists:
        return JsonResponse({
            'available': False,
            'message': 'این نام انگلیسی قبلاً انتخاب شده است'
        })
    else:
        return JsonResponse({
            'available': True,
            'message': 'نام انگلیسی قابل استفاده است',
            'menu_url': f'/menu/{english_name}'
        })



# views.py - اضافه کردن ویو جدید
@login_required
@restaurant_owner_required
def get_category_tree(request, slug):
    """دریافت درخت دسته‌بندی‌ها به صورت سلسله‌مراتبی"""
    try:
        # دریافت فقط دسته‌بندی‌های مادر (parent=None)
        parent_categories = Category.objects.filter(
            parent=None,
            isActive=True
        ).prefetch_related('children').order_by('displayOrder')

        categories_data = []
        for parent in parent_categories:
            parent_data = {
                'id': parent.id,
                'title': parent.title,
                'image_url': parent.image.url if parent.image else '',
                'has_children': parent.is_parent,
                'subcategories': []
            }

            # اضافه کردن زیردسته‌ها
            for child in parent.active_subcategories:
                child_data = {
                    'id': child.id,
                    'title': child.title,
                    'image_url': child.image.url if child.image else '',
                    'parent_title': parent.title
                }
                parent_data['subcategories'].append(child_data)

            categories_data.append(parent_data)

        return JsonResponse({
            'success': True,
            'categories': categories_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در دریافت دسته‌بندی‌ها: {str(e)}'
        })



# views.py - ویو برای افزودن سریع دسته‌بندی
@login_required
@restaurant_owner_required
@csrf_exempt
@require_http_methods(["POST"])
def quick_add_menu_category(request, slug):
    """افزودن سریع دسته‌بندی به منوی رستوران"""
    restaurant = request.restaurant

    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')

        if not category_id:
            return JsonResponse({
                'success': False,
                'message': 'لطفاً یک دسته‌بندی انتخاب کنید'
            })

        # بررسی وجود دسته‌بندی
        category = get_object_or_404(Category, id=category_id, isActive=True)

        # بررسی تکراری نبودن
        if MenuCategory.objects.filter(restaurant=restaurant, category=category).exists():
            return JsonResponse({
                'success': False,
                'message': 'این دسته‌بندی قبلاً به منو اضافه شده است'
            })

        # ایجاد دسته‌بندی منو
        menu_category = MenuCategory(
            restaurant=restaurant,
            category=category,
            isActive=True
        )
        menu_category.save()

        return JsonResponse({
            'success': True,
            'message': 'دسته‌بندی با موفقیت به منو اضافه شد',
            'menu_category': {
                'id': menu_category.id,
                'title': category.title,
                'image_url': menu_category.displayImage.url if menu_category.displayImage else '',
                'has_custom_image': bool(menu_category.customImage)
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در افزودن دسته‌بندی: {str(e)}'
        })




@login_required
def user_menus_view(request):
    # رستوران‌هایی که مالک آن‌ها کاربر فعلی است
    user_restaurants = request.user.restaurants.all()

    # منوهای مربوط به همان رستوران‌ها
    menu_categories = MenuCategory.objects.filter(
        restaurant__in=user_restaurants
    ).select_related('restaurant', 'category')

    return render(request, 'panel_app/free/myMenu.html', {
        'menu_categories': menu_categories,
    })


    # views.py
import qrcode
import base64
from io import BytesIO
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

@login_required
def generate_qr_code(request, restaurant_slug):
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, owner=request.user)

    # ساخت آدرس کامل منو
    menu_url = request.build_absolute_uri(f'/menu/{restaurant.slug}/')

    # تولید QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(menu_url)
    qr.make(fit=True)

    # تبدیل به تصویر
    img = qr.make_image(fill_color="black", back_color="white")

    # ذخیره در بافر
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    # تبدیل به base64 برای نمایش در HTML
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return JsonResponse({
        'success': True,
        'qr_code': f'data:image/png;base64,{img_str}',
        'menu_url': menu_url
    })



@login_required
def check_pending_restaurant(request):
    """بررسی وجود رستوران در حال انتظار"""
    pending_restaurant = request.session.get('pending_restaurant')

    if pending_restaurant:
        return JsonResponse({
            'has_pending': True,
            'data': pending_restaurant
        })
    else:
        return JsonResponse({
            'has_pending': False
        })

@login_required
def clear_pending_restaurant(request):
    """پاک کردن رستوران در حال انتظار"""
    if 'pending_restaurant' in request.session:
        del request.session['pending_restaurant']

    return JsonResponse({'success': True})





