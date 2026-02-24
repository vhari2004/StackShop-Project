from django.shortcuts import render,redirect
from core.decorators import seller_required
from django.contrib.auth.decorators import login_required
from .models import SellerProfile

@login_required
def seller_profile_view(request):
    profile = SellerProfile.objects.filter(user=request.user).first()

    if not profile:
        return redirect("login")

    return render(request, "seller/sellerprofilepage.html", {"profile": profile})
@login_required
def seller_profile_create(request):

    if SellerProfile.objects.filter(user=request.user).exists():
        return redirect("seller-profile")

    if request.method == "POST":
        store_name = request.POST.get("store_name")
        gst_number = request.POST.get("gst_number")
        pan_number = request.POST.get("pan_number")
        bank_account_number = request.POST.get("bank_account_number")
        ifsc_code = request.POST.get("ifsc_code")
        business_address = request.POST.get("business_address")
        store_image = request.FILES.get("store_image")


# Create your views here.
