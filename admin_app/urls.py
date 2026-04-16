from django.urls import path
from . import views

urlpatterns = [
    path('admin_dashboard', views.admin_dashboard_view, name='admin_dashboard'),
    path('sellerverification/<int:id>/',views.seller_verification,name='sellerverification'),
    path('productverification/<int:id>/', views.product_verification, name='productverification'),
    # Category/Subcategory and Banner Management (non-admin namespace to avoid Django admin route conflict)
    path('dashboard/save-category/', views.save_category, name='save_category'),
    path('dashboard/save-subcategory/', views.save_subcategory, name='save_subcategory'),
    path('dashboard/save-banner/', views.save_banner, name='save_banner'),
    path('add-deal/', views.add_deal, name='add_deal'),
    path('edit-deal/<int:id>/', views.edit_deal, name='edit_deal'),
    path('manage-deals/', views.manage_deals, name='manage_deals'),
    path('delete-deal/', views.delete_deal, name='delete_deal'),
    path('reactivation/approve/<int:request_id>/', views.approve_reactivation_request, name='approve_reactivation_request'),
    path('reactivation/reject/<int:request_id>/', views.reject_reactivation_request, name='reject_reactivation_request'),
    path('dashboard/toggle-product-active/', views.toggle_product_active, name='toggle_product_active'),
    path('dashboard/toggle-seller-active/', views.toggle_seller_active, name='toggle_seller_active'),
    path('dashboard/save-deal/', views.add_deal, name='save_deal'),
]