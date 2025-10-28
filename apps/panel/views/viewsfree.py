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

@login_required
def panel(request):
    """پنل اصلی - نمایش رستوران‌های کاربر"""
    user_restaurants = Restaurant.objects.filter(owner=request.user, isActive=True)

    context = {
        'restaurants': user_restaurants,
        'has_restaurant': user_restaurants.exists()
    }

    print(user_restaurants.exists())
    return render(request, 'panel_app/free/panel.html', context)

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




# views.py
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_restaurant_modal(request):
    """مدیریت افتتاح رستوران از طریق مودال"""
    try:
        data = json.loads(request.body)

        # مرحله 1: دریافت نام و نام خانوادگی و نام رستوران
        if data.get('step') == 1:
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
            request.session.modified = True  # این خط مهم است

            return JsonResponse({
                'success': True,
                'message': 'اطلاعات با موفقیت ذخیره شد',
                'next_step': 2
            })

        # مرحله 2: دریافت نام انگلیسی
        elif data.get('step') == 2:
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

        # مرحله نهایی: ایجاد رستوران
        elif data.get('step') == 3:
            # دریافت مستقیم داده‌ها از request
            name = data.get('name', '').strip()
            family = data.get('family', '').strip()
            restaurant_name = data.get('restaurant_name', '').strip()
            english_name = data.get('english_name', '').strip().lower()

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

