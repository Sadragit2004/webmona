
from django.contrib import admin
from django.urls import path
import web.settings as sett
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
]+static(sett.MEDIA_URL,document_root = sett.MEDIA_ROOT)
