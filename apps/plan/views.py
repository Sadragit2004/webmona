from django.shortcuts import render, get_object_or_404,redirect
from django.views.generic import ListView, DetailView
from .models import Plan
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from django.contrib import messages
from django.utils import timezone
from .models import Plan, PlanOrder
from apps.product.models import Product

@login_required



def plan_list(request):
    plans = Plan.objects.filter(isActive=True).prefetch_related('features').order_by('price')

    context = {
        'plans': plans
    }
    return render(request, 'plan_app/plan_list.html', context)



@login_required
def purchase_plan(request, plan_slug):
    """انتخاب پلن و اضافه کردن به سبد خرید (بدون پرداخت)"""
    plan = get_object_or_404(Plan, slug=plan_slug, isActive=True)

    # بررسی آیا کاربر همین پلن رو قبلاً انتخاب کرده و پرداخت نکرده
    existing_unpaid_order = PlanOrder.objects.filter(
        user=request.user,
        plan=plan,
        isPaid=False  # فقط بررسی پلن‌های پرداخت نشده
    ).first()

    if existing_unpaid_order:
        messages.info(request, 'این پلن قبلاً در سبد خرید شما وجود دارد')
        return redirect('plan:shop_cart')

    # ایجاد سفارش با وضعیت پرداخت نشده
    plan_order = PlanOrder.objects.create(
        plan=plan,
        user=request.user,
        finalPrice=plan.price if plan.price else 0,
        isPaid=False,  # مهم: ابتدا False باشد
        paidAt=None    # پرداخت نشده
    )

    messages.success(request, f'پلن {plan.name} به سبد خرید اضافه شد')
    return redirect('plan:shop_cart')  # هدایت به سبد خرید


# apps/plan/views.py
@login_required
def shop_cart(request):
    """
    نمایش سبد خرید کاربر با آخرین پلن انتخابی (پرداخت نشده) و محصولات
    """
    # دریافت آخرین پلن پرداخت نشده کاربر
    latest_plan_order = PlanOrder.objects.filter(
        user=request.user,
        isPaid=False  # فقط پلن‌های پرداخت نشده
    ).select_related('plan').order_by('-createdAt').first()

    # دریافت محصولات فعال به همراه گالری و ویژگی‌ها
    products = Product.objects.filter(
        is_active=True
    ).prefetch_related(
        'features',
        'gallery'
    ).order_by('-publish_date')

    selected_plan = None
    plan_cost = 0
    stands_cost = 0
    tax_cost = 0
    total_cost = 0

    if latest_plan_order:
        selected_plan = latest_plan_order.plan
        plan_cost = selected_plan.price if selected_plan.price else 0

        # محاسبات مالی
        stands_cost = 0
        tax_cost = int((plan_cost + stands_cost) * 0.09)
        total_cost = plan_cost + stands_cost + tax_cost

    context = {
        'selected_plan': selected_plan,
        'plan_cost': plan_cost,
        'stands_cost': stands_cost,
        'tax_cost': tax_cost,
        'total_cost': total_cost,
        'latest_plan_order': latest_plan_order,
        'products': products,  # اضافه کردن محصولات به context
    }

    return render(request, 'plan_app/shop_cart.html', context)


@require_POST
@login_required
def update_cart(request):
    """
    به‌روزرسانی سبد خرید
    """
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = data.get('quantity')

        # اینجا منطق به‌روزرسانی سبد خرید در دیتابیس

        return JsonResponse({
            'success': True,
            'message': 'سبد خرید با موفقیت به‌روزرسانی شد'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در به‌روزرسانی سبد خرید'
        })

@require_POST
@login_required
def remove_from_cart(request):
    """
    حذف محصول از سبد خرید
    """
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')

        # اینجا منطق حذف محصول از سبد خرید در دیتابیس

        return JsonResponse({
            'success': True,
            'message': 'محصول با موفقیت از سبد خرید حذف شد'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در حذف محصول از سبد خرید'
        })

@require_POST
@login_required
def clear_cart(request):
    """
    خالی کردن سبد خرید
    """
    try:
        # اینجا منطق خالی کردن سبد خرید در دیتابیس

        return JsonResponse({
            'success': True,
            'message': 'سبد خرید با موفقیت خالی شد'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در خالی کردن سبد خرید'
        })