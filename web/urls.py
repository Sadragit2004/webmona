
from django.contrib import admin
from django.urls import path,include
import web.settings as sett
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('apps.main.urls'),name='main'),
    path('account/',include('apps.user.urls',namespace='account')),
    path('menu/',include('apps.menu.urls.url',namespace='menu')),
    path('panel/',include('apps.panel.urls',namespace='panel'))

]+static(sett.MEDIA_URL,document_root = sett.MEDIA_ROOT)
