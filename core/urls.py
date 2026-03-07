from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('search/', views.search_and_filter_view, name='search'),
    path('login/',views.login_view,name='login'),
    path('register/',views.register_view,name='register'),
    path('logout/',views.logout_view,name='logout'),
    path('category/',views.category_view,name='category'),
    path('catogory_list/',views.category_list_view,name='catogory_list'),
    path('deals/',views.deals_view,name='deals'),
]
