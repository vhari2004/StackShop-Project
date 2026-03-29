from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('search/', views.search_and_filter_view, name='search'),
    path('login/',views.login_view,name='login'),
    path('reactivation-request/', views.reactivation_request_view, name='reactivation_request'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_view, name='reset_password'),
    path('register/',views.register_view,name='register'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('resend-email-otp/', views.resend_email_otp_view, name='resend_email_otp'),
    path('logout/',views.logout_view,name='logout'),
    path('category/',views.category_view,name='category'),
    path('catogory_list/',views.category_list_view,name='catogory_list'),
    path('deals/',views.deals_view,name='deals'),
    path('about-us/', views.about_us_view, name='about_us'),
    path('our-story/', views.our_story_view, name='our_story'),
    path('careers/', views.careers_view, name='careers'),
    path('blog/', views.blog_view, name='blog'),
    path('contact-us/', views.contact_us_view, name='contact_us'),
    path('shipping-info/', views.shipping_info_view, name='shipping_info'),
    path('returns-policy/', views.returns_policy_view, name='returns_policy'),
    path('faq/', views.faq_view, name='faq'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions_view, name='terms_conditions'),
    path('sitemap/', views.sitemap_view, name='sitemap'),
]
