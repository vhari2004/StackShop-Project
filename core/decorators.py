from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)
        if request.user.is_admin != True:
            return HttpResponse("Forbidden", status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
def seller_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated and request.user.is_admin:
            messages.error(request,'Unauthorized !! user not authenticated')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        if request.user.role != 'SELLER':
            messages.error(request,'Forbidden !! user not a Seller')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        return view_func(request, *args, **kwargs)
    return _wrapped_view
def verified_seller_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request,'Unauthorized !! user not authenticated')
            return redirect('seller-profile')
        if request.user.role != 'SELLER':
            messages.error(request,'Unauthorized !! Not a Seller')
            return redirect('seller-profile')        
        if not getattr(request.user, "is_verified_seller", False):
            messages.error(request,'Unauthorized !! not a verified seller')
            return redirect('seller-profile')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def customer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.is_admin or request.user.role=="SELLER":
            messages.warning(request,'not a customer')
            return redirect(request.META.get('HTTP_REFERER','/'))
        if request.user.role != "CUSTOMER":
            return HttpResponse("Forbidden", status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
