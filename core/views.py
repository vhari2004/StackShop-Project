from django.shortcuts import render,redirect
from .models import CustomUser
from django.contrib.auth import login,logout,authenticate
# from django.contrib.auth.decorators import login_required
from core.decorators import admin_required,customer_required,seller_required

def home_view(request):
    user=request.user
    if user.is_authenticated:
        return render(request,'core_templates/homepage.html',{'user':user})
    return render(request,'core_templates/homepage.html')

def register_view(request):
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
            return redirect('profile')
        else:
            return redirect('login')
    return render(request,'core_templates/loginpage.html')

@customer_required
def user_profile_view(request):
    user=request.user
    return render(request,'profile.html',{"user":user})

# Create your views here.
