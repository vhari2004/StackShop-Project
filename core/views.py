from django.shortcuts import render,redirect
from .models import CustomUser
from django.contrib.auth import login,logout,authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.decorators import admin_required,seller_required
from customer.models import Cart,CartItem
from .models import *

def home_view(request):
    user=request.user
    category_items=Category.objects.all()
    if user.is_authenticated:
        cart=Cart.objects.filter(user=user).first()
        cart_items=CartItem.objects.filter(cart=cart).prefetch_related('variant__product__subcategory','variant__images')
        return render(request,'core_templates/homepage.html',{'user':user,'cart_items':cart_items,'categories':category_items})
    return render(request,'core_templates/homepage.html',{'categories':category_items})

def category_list_view(request):
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories')
    context = {
        'categories': categories
    }
    return render(request, 'core_templates/categories.html', context)
def register_view(request):
    role=request.GET.get('role')
    if request.method=="POST":
        username=request.POST.get('username')
        email=request.POST.get('email')
        password=request.POST.get('password')
        confirm_password=request.POST.get('confirm_password')
        if password != confirm_password:
            messages.error(request,'passwords doesnot match')
            return render(request,'core_templates/registerpage.html',{'username': username,'email': email})
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request,'Invalid username !')
            return render(request,'core_templates/registerpage.html',{'username': username,'email': email})
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request,'Invalid email !')
            return render(request,'core_templates/registerpage.html',{'username': username,'email': email})
        if role == 'seller':
            store_name = request.POST.get('store_name')
            store_slug = request.POST.get('store_slug')
            business_address = request.POST.get('business_address')
            gst_number = request.POST.get('gst_number')
            pan_number = request.POST.get('pan_number')
            bank_account_number = request.POST.get('bank_account_number')
            ifsc_code = request.POST.get('ifsc_code')
            user=CustomUser.objects.create_user(username=username,email=email,password=password,role='SELLER')
        else:
            user=CustomUser.objects.create_user(username=username,email=email,password=password)
            user.save()
        return redirect('login')
    return render(request,'core_templates/registerpage.html')

def login_view(request):
    if request.method=="POST":
        username=request.POST.get('usernameoremail')
        password=request.POST.get('password')
        try:
            user_obj = CustomUser.objects.get(email=username)
            username = user_obj.username
        except CustomUser.DoesNotExist:
            username = username
        user=authenticate(username=username,password=password )
        if user is not None:
            login(request,user)
            messages.success(request,'user successgully logined')
            if user.is_admin:
                return redirect('admin_dashboard')
            return redirect('home')
        else:
            messages.error(request,'invalid credintials !')
    return render(request,'core_templates/loginpage.html')
def logout_view(request):
    logout(request)
    return redirect('home')
def category_view(request):
    cart=Cart.objects.filter(user=request.user).first()
    cart_items=CartItem.objects.filter(cart=cart).prefetch_related('variant__product__subcategory','variant__images')
    return render(request,'core_templates/categories.html',{'cart_items':cart_items})
def deals_view(request):
    cart=Cart.objects.filter(user=request.user).first()
    cart_items=CartItem.objects.filter(cart=cart).prefetch_related('variant__product__subcategory','variant__images')
    return render(request,'core_templates/dealspage.html',{'cart_items':cart_items})



# Create your views here.
