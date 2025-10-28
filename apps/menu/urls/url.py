from django.urls import path
from ..views.freemenuviews.views import digital_menu, get_foods_by_category, search_foods, change_language

app_name = 'menu'
urlpatterns = [
    path('<slug:restaurant_slug>/', digital_menu, name='digital_menu'),
    path('<slug:restaurant_slug>/category/<str:category_id>/', get_foods_by_category, name='foods_by_category'),
    path('<slug:restaurant_slug>/search/', search_foods, name='search_foods'),
    path('<slug:restaurant_slug>/change-language/', change_language, name='change_language'),
]