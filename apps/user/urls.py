from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path("login/", views.send_mobile, name="send_mobile"),
    path("verify/", views.verify_code, name="verify_code"),
    path("logout/", views.user_logout, name="logout"),
]
