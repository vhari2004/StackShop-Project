from django.urls import path
from . import views

urlpatterns = [
    # user profile and dashboard----------------------
    path('profile/',views.user_profile_view,name='profile'),
    path('customer_dashboard/',views.customer_dashboard_view,name='customer_dashboard'),
    #------------------------------------------------------------

    # product views----------------------
    path('products/',views.product_list_view,name='product_list'),
    path('productsingle/',views.product_single_view,name='productsingle'),
    #------------------------------------------------------------

    # for wishlist----------------------
    path('wishlist/',views.wishlist_view,name='wishlist'),
    path('addwishlist/<int:id>/',views.add_wishlist_view,name='addwishlist'),
    path('removewishlist/<int:id>/',views.remove_wishlist_view,name='removewishlist'),
    path('createcollection/',views.create_collection_view,name='createcollection'),
    path('updatecollection/', views.update_collection_view, name='updatecollection'),   
    path('deletecollection/<int:wishlist_id>/', views.delete_collection_view, name='deletecollection'), 
    #-------------------------------------------------------------------------------

    # order history and address----------------------
    path('order-history/',views.orderhistory_view,name='order-history'),
    path('address/',views.address_view,name='address'),
    #------------------------------------------------------------
]
