from django.urls import path
from . import views

urlpatterns = [
    path('seller_bridge/', views.seller_bridge, name='seller-bridge'),
    path('becomeseller',views.seller_broche_view,name="becomeseller"),
]
