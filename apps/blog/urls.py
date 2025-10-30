from django.urls import path
from .views import *

app_name = 'blog'
urlpatterns = [

    path('',Show_All_blog.as_view(),name='show_blog'),
    path('<str:slug>/',Blog_detail.as_view(),name='detail'),
    path('blog-list/',BlogsView.as_view(),name='blogs')

]
