# urls.py
from django.urls import path
from .views import viewsfree

app_name = 'panel'

urlpatterns = [
    path('', viewsfree.panel, name='panel'),
    path('create/', viewsfree.create_restaurant, name='create_restaurant'),
    path('create-modal/', viewsfree.create_restaurant_modal, name='create_restaurant_modal'),
    path('check-english-name/', viewsfree.check_english_name, name='check_english_name'),
    path('<str:slug>/admin/', viewsfree.restaurant_admin, name='restaurant_admin'),
    path('<str:slug>/foods/add/', viewsfree.add_food, name='add_food'),
    path('<str:slug>/foods/<int:food_id>/update/', viewsfree.update_food, name='update_food'),
    path('<str:slug>/foods/<int:food_id>/delete/', viewsfree.delete_food, name='delete_food'),
    path('<str:slug>/foods/<int:food_id>/toggle/', viewsfree.toggle_food_status, name='toggle_food_status'),
    path('<str:slug>/menu-categories/add/', viewsfree.add_menu_category, name='add_menu_category'),
    path('<str:slug>/menu-categories/<int:menu_category_id>/toggle/', viewsfree.toggle_menu_category_status, name='toggle_menu_category_status'),
    path('<str:slug>/menu-categories/<int:menu_category_id>/delete/', viewsfree.delete_menu_category, name='delete_menu_category'),
    path('<str:slug>/settings/update/', viewsfree.update_restaurant_settings, name='update_restaurant_settings'),
    path('<str:slug>/foods/category/<str:category_id>/', viewsfree.get_foods_by_category, name='get_foods_by_category'),
    path('<str:slug>/foods/update-order/', viewsfree.update_food_order, name='update_food_order'),
    path('<slug:slug>/categories/tree/', viewsfree.get_category_tree, name='category-tree'),
    path('<slug:slug>/categories/quick-add/', viewsfree.quick_add_menu_category, name='quick-add-category'),
    path('my-menus/', viewsfree.user_menus_view, name='user_menus'),
    path('generate-qr/<slug:restaurant_slug>/', viewsfree.generate_qr_code, name='generate_qr'),
    path('check-pending-restaurant/', viewsfree.check_pending_restaurant, name='check_pending_restaurant'),
    path('clear-pending-restaurant/', viewsfree.clear_pending_restaurant, name='clear_pending_restaurant'),
    path('orders/<int:order_id>/', viewsfree.order_detail, name='order_detail'),
    path('orders/<int:order_id>/update-status/', viewsfree.update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/payment/', viewsfree.process_payment, name='process_payment'),
    path('orders/<int:order_id>/cancel/', viewsfree.cancel_order, name='cancel_order'),

]