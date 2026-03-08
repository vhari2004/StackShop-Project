from django.urls import path
from . import views

urlpatterns = [
    path('seller_bridge/', views.seller_bridge, name='seller-bridge'),
    path('becomeseller/',views.seller_broche_view,name="becomeseller"),
    path('seller_bridge/', views.seller_bridge, name='seller-bridge'),
    path('sellerprofile',views.seller_profile_view,name='seller-profile'),
    path("add-product/", views.add_product, name="add-product"),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path("update-product/<int:product_id>/", views.update_product, name="update_product"),
    path("delete-product/<int:product_id>/",views.delete_product,name="delete_product"),
    path("seller_customers_orders/", views.seller_customers_orders, name="seller_customers_orders"),
    path('customer_reviews/',views.customer_reviews,name='customer_reviews'),
]
