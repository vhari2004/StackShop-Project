from django.urls import path
from . import views

urlpatterns = [
    # user profile and dashboard----------------------
    path('profile/',views.user_profile_view,name='profile'),
    path('customer_dashboard/',views.customer_dashboard_view,name='customer_dashboard'),
    #------------------------------------------------------------

    # product views----------------------
    path('products/',views.product_list_view,name='product_list'),
    path('productsingle/<int:id>',views.product_single_view,name='productsingle'),
    #------------------------------------------------------------

    # for wishlist----------------------
    path('wishlist/',views.wishlist_view,name='wishlist'),
    path('addwishlist/<int:id>/',views.add_wishlist_view,name='addwishlist'),
    path('removewishlist/<int:id>/',views.remove_wishlist_view,name='removewishlist'),
    path('createcollection/',views.create_collection_view,name='createcollection'),
    path('updatecollection/', views.update_collection_view, name='updatecollection'),   
    path('deletecollection/<int:wishlist_id>/', views.delete_collection_view, name='deletecollection'), 
    #-------------------------------------------------------------------------------
    
    # for cart----------------------
    path('cart/',views.cart_view,name='cart_view'),
    path('addtocart/<int:id>/',views.add_to_cart_view,name='add_to_cart'),
    path('removefromcart/<int:id>',views.remove_from_cart_view,name='remove_from_cart'),
    path('updatecart/<int:id>/',views.update_cart_view,name='update_cart'),
    path('checkout/',views.checkout_view,name='checkout'),
    #----------------------------------------------------------------------------

    # for address----------------------
    path('add-address/',views.add_address_view,name='add_address'),
    path('address/',views.address_view,name='address'),
    path('update-address/',views.update_address_view,name='update_address'),
    path('delete-address/<int:address_id>/',views.delete_address_view,name='delete_address'),
    path('set-default-address/',views.set_default_address_view,name='set_default_address'),
    #----------------------------------------------------------------------------

    # order history and address----------------------
    path('order-history/',views.order_history_view,name='order-history'),
    #------------------------------------------------------------
    # payment processing and success----------------------
    path("payment-success/",views.payment_success,name="payment_success"),
    path("order-success/",views.order_success,name="order_success"),
    #------------------------------------------------------------
]
