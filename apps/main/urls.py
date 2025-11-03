from . import views


from django.urls import path

app_name = 'main'

urlpatterns = [


    path('',views.main,name='index'),
    path('content/', views.main_content_view, name='block'),


]