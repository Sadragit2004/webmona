
from django.contrib import admin
from django.urls import path,include
import web.settings as sett
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('apps.main.urls'),name='main'),
    path('accounts/',include('apps.user.urls',namespace='account')),
    path('menu/',include('apps.menu.urls.url',namespace='menu')),
    path('panel/',include('apps.panel.urls',namespace='panel')),
     path('ckeditor',include('ckeditor_uploader.urls')),
     path('blog/',include('apps.blog.urls',namespace='blog'))

]+static(sett.MEDIA_URL,document_root = sett.MEDIA_ROOT)
