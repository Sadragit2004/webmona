from django.shortcuts import render,redirect
import requests
import json
import requests
from django.views import View
from django.contrib import messages
from apps.order.models import Ordermenu
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from apps.peyment.models import Peyment
from apps.user.models import CustomUser
import utils
from django.contrib.auth.decorators import login_required

from .zarinpal import ZarinPal
from django.http import JsonResponse

ZP_API_REQUEST = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = "https://www.zarinpal.com/pg/StartPay/{authority}"

pay = ZarinPal(merchant='41cb2cdd-3a44-4fb4-a0b3-db471b673078', call_back_url="https://rank0.ir/peyment/verify/")
merchant='41cb2cdd-3a44-4fb4-a0b3-db471b673078'

# views.py - ویوهای پرداخت
@login_required
def send_request(request, order_id):
    """ارسال درخواست پرداخت برای سفارش منو"""
    if utils.has_internet_connection():
        try:
            user = request.user
            order = Ordermenu.objects.get(id=order_id, restaurant__owner=user)

            # ایجاد رکورد پرداخت
            peyment = Peyment.objects.create(
                order=order,
                customer=request.user,
                amount=order.get_fixed_price(),
                description='پرداخت هزینه ساخت منو توسط شرکت'
            )

            peyment.save()

            # ذخیره در session
            request.session['peyment_session'] = {
                'order_id': order.id,
                'peyment_id': peyment.id,
            }
            request.session.modified = True

            # ارسال درخواست به درگاه پرداخت
            from .zarinpal import ZarinPal
            pay = ZarinPal(merchant='41cb2cdd-3a44-4fb4-a0b3-db471b673078',
                          call_back_url="https://rank0.ir/peyment/verify/")

            response = pay.send_request(
                amount=order.get_fixed_price(),
                description='هزینه ساخت منو دیجیتال',
                email=user.email if user.email else "Example@test.com",
                mobile=user.mobileNumber
            )

            if response.get('error_code') is None:
                return response  # redirect به درگاه
            else:
                messages.error(request, f'خطا در اتصال به درگاه پرداخت: {response.get("message")}')
                return redirect('panel:panel')

        except Ordermenu.DoesNotExist:
            messages.error(request, 'سفارش یافت نشد')
            return redirect('panel:panel')
        except Exception as e:
            messages.error(request, f'خطا در پردازش پرداخت: {str(e)}')
            return redirect('panel:panel')
    else:
        messages.error(request, 'اتصال اینترنت شما قابل تایید نیست', 'danger')
        return redirect('panel:panel')


class Zarin_pal_view_verfiy(LoginRequiredMixin, View):
    def get(self, request):
        t_status = request.GET.get('Status')
        t_authority = request.GET['Authority']
        order_id = request.session['peyment_session']['order_id']
        peyment_id = request.session['peyment_session']['peyment_id']
        order = Ordermenu.objects.get(id=order_id)
        peyment = Peyment.objects.get(id=peyment_id)

        if t_status == 'OK':
            req_header = {
                "accept": "application/json",
                "content-type": "application/json"
            }
            req_data = {
                "merchant_id": merchant,
                "amount": order.get_fixed_price(),
                "authority": t_authority
            }
            req = requests.post(url=ZP_API_VERIFY, data=json.dumps(req_data), headers=req_header)

            if len(req.json()['errors']) == 0:
                t_status_code = req.json()['data']['code']

                if t_status_code == 100:
                    # پرداخت موفق - بروزرسانی وضعیت سفارش
                    order.isfinaly = True
                    order.status = Ordermenu.STATUS_PAID
                    order.isActive = True
                    order.save()

                    peyment.isFinaly = True
                    peyment.statusCode = t_status_code
                    peyment.refId = str(req.json()['data']['refId'])
                    peyment.save()

                    # پاک کردن session
                    if 'peyment_session' in request.session:
                        del request.session['peyment_session']
                    if 'pending_order' in request.session:
                        del request.session['pending_order']

                    return redirect('peyment:show_verfiy_message', 'کد رهگیری شما : {}'.format(str(req.json()['data']['refId'])))


                elif t_status_code == 101:
                    # پرداخت تکراری - بروزرسانی وضعیت
                    order.isfinaly = True
                    order.status = Ordermenu.STATUS_PAID
                    order.isActive = True
                    order.save()

                    peyment.isFinaly = True
                    peyment.statusCode = t_status_code
                    peyment.refId = str(req.json()['data']['refId'])
                    peyment.save()

                    return redirect('peyment:show_verfiy_message', 'کد رهگیری شما : {}'.format(str(req.json()['data']['refId'])))

                else:
                    peyment.statusCode = t_status_code
                    peyment.save()
                    return redirect('peyment:show_verfiy_unmessage', 'پرداخت ناموفق بود')

            else:
                e_code = req.json()['errors']['code']
                e_message = req.json()['errors']['message']
                return JsonResponse({
                    "status": 'ok',
                    "message": e_message,
                    "error_code": e_code
                })

        else:
            order.status = Ordermenu.STATUS_UNPAID
            order.save()
            return redirect('peyment:show_verfiy_unmessage', 'پرداخت توسط کاربر لغو شد')


def show_verfiy_message(request, message):
    """نمایش پیام موفقیت پرداخت"""
    order = Ordermenu.objects.all()
    return render(request, 'peyment_app/peyment.html', {'message': message, 'orders': order})


def show_verfiy_unmessage(request, message):
    """نمایش پیام عدم موفقیت پرداخت"""
    return render(request, 'peyment_app/unpeyment.html', {'message': message})