from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import IntegrityError

from datetime import timedelta

from .forms import MobileForm, VerificationCodeForm
from .models import CustomUser, UserSecurity

# ✅ ایمپورت توابع از validators (utils)
from .validators.model import generate_activation_code, validate_activation_code


# ======================
# 📱 مرحله 1: ورود شماره موبایل
# ======================
def send_mobile(request):
    next_url = request.GET.get("next")  # دریافت آدرس مقصد بعد از ورود
    if request.method == "POST":
        form = MobileForm(request.POST)
        if form.is_valid():
            mobile = form.cleaned_data['mobileNumber']

            try:
                # بررسی یا ساخت کاربر جدید
                user, created = CustomUser.objects.get_or_create(mobileNumber=mobile)

                if created:
                    user.is_active = False
                    user.save()

                # مدیریت UserSecurity با کنترل خطا
                try:
                    security = UserSecurity.objects.get(user=user)
                except UserSecurity.DoesNotExist:
                    security = UserSecurity.objects.create(user=user)

                # تولید کد فعال‌سازی و زمان انقضا
                code = generate_activation_code(5)
                expire_time = timezone.now() + timedelta(minutes=2)

                # ذخیره در مدل امنیتی
                security.activeCode = code
                security.expireCode = expire_time
                security.isBan = False
                security.save()

                # TODO: ارسال پیامک (در حال حاضر در کنسول)
                print(f"کد تأیید برای {mobile}: {code}")

                # ذخیره شماره موبایل و آدرس بعدی در session
                request.session["mobileNumber"] = mobile
                if next_url:
                    request.session["next_url"] = next_url

                # هدایت به صفحه وارد کردن کد
                return redirect("account:verify_code")

            except IntegrityError:
                # اگر خطای تکراری بود، دوباره امتحان کن
                security = UserSecurity.objects.get(user=user)
                # تولید کد فعال‌سازی و زمان انقضا
                code = generate_activation_code(5)
                expire_time = timezone.now() + timedelta(minutes=2)

                # ذخیره در مدل امنیتی
                security.activeCode = code
                security.expireCode = expire_time
                security.isBan = False
                security.save()

                # ذخیره شماره موبایل و آدرس بعدی در session
                request.session["mobileNumber"] = mobile
                if next_url:
                    request.session["next_url"] = next_url

                return redirect("account:verify_code")

    else:
        form = MobileForm()

    return render(request, "user_app/login.html", {"form": form, "next": next_url})


# ======================
# 🔒 مرحله 2: تأیید کد فعال‌سازی
# ======================
def verify_code(request):
    mobile = request.session.get("mobileNumber")
    next_url = request.session.get("next_url")

    if not mobile:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'شماره موبایل یافت نشد'})
        return redirect("account:send_mobile")

    try:
        user = CustomUser.objects.get(mobileNumber=mobile)
        security = UserSecurity.objects.get(user=user)
    except CustomUser.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'کاربری با این شماره موبایل یافت نشد'})
        messages.error(request, "کاربری با این شماره موبایل یافت نشد.")
        return redirect("account:send_mobile")
    except UserSecurity.DoesNotExist:
        # اگر UserSecurity وجود نداشت، ایجادش کن
        security = UserSecurity.objects.create(user=user)

    if request.method == "POST":

        # ======================
        # ارسال مجدد کد
        # ======================
        if "resend" in request.POST and request.POST["resend"] == "true":
            code = generate_activation_code(5)
            expire_time = timezone.now() + timedelta(minutes=2)

            security.activeCode = code
            security.expireCode = expire_time
            security.isBan = False
            security.save()

            print(f"🔄 کد جدید برای {mobile}: {code}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'کد جدید ارسال شد'})

            messages.success(request, "کد جدید ارسال شد ✅")
            return redirect("account:verify_code")

        # ======================
        # بررسی کد واردشده
        # ======================
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['activeCode']

            # بررسی زمان انقضا
            if security.expireCode:
                if timezone.is_naive(security.expireCode):
                    expire_time = timezone.make_aware(security.expireCode)
                else:
                    expire_time = security.expireCode

                if expire_time < timezone.now():
                    messages.error(request, "⏳ کد منقضی شده است، دوباره تلاش کنید.")
                    return redirect("account:send_mobile")

            # بررسی صحت کد با تابع validate_activation_code
            try:
                validate_activation_code(security, code)
            except Exception as e:
                messages.error(request, f"❌ {e}")
                return redirect("account:verify_code")

            # ✅ فعال‌سازی کاربر
            user.is_active = True
            user.save()

            # پاک‌سازی کد از پایگاه داده
            security.activeCode = None
            security.expireCode = None
            security.save()

            login(request, user)
            messages.success(request, "✅ ورود با موفقیت انجام شد.")

            if next_url:
                return redirect(next_url)
            return redirect("main:index")

    else:
        form = VerificationCodeForm()

    return render(request, "user_app/code.html", {"form": form, "mobile": mobile})


# ======================
# 🚪 خروج کاربر
# ======================
def user_logout(request):
    logout(request)
    messages.success(request, "✅ شما با موفقیت از حساب کاربری خارج شدید.")
    return redirect("main:index")