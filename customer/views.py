from urllib import request

from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from seller.models import Product,ProductVariant
from customer.models import Wishlist,WishlistItem
from django.contrib import messages
from django.shortcuts import get_object_or_404
# userlogin-----------------------------------------------------------------------------

@login_required
def user_profile_view(request):
    user=request.user
    if request.method=="POST":
        first_name=request.POST.get('first_name')
        last_name=request.POST.get('last_name')
        phone=request.POST.get('phone')
        image=request.FILES.get('profile_photo')
        user.first_name=first_name
        user.last_name=last_name
        user.phone_number=phone
        if image:
            user.profile_image=image
        user.save()
    return render(request,'customer_templates/profile.html',{"user":user})
#------------------------------------------------------------------------------

# wishlist---------------------------------------------------------------------
@login_required
def add_wishlist_view(request, id):
    product_variant = get_object_or_404(ProductVariant, id=id)
    try:
        wishlist = Wishlist.objects.get(user=request.user, is_default=True)
    except Wishlist.DoesNotExist:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user,wishlist_name=f"{request.user.username}'s Wishlist",is_default=True)
        if created:
            messages.success(request, f"( {wishlist.wishlist_name} ) created.")
        return redirect('product_list')
    if WishlistItem.objects.filter(wishlist=wishlist, variant=product_variant).exists():
        messages.error(request, f"Product already in ( {wishlist.wishlist_name} ).")
        return redirect('product_list')
    else:
        WishlistItem.objects.get_or_create(wishlist=wishlist, variant=product_variant)
        messages.success(request, f"Product added to ( {wishlist.wishlist_name} ).")
        return redirect('product_list')
@login_required
def remove_wishlist_view(request, id):
    wishlist_item = get_object_or_404(WishlistItem, id=id, wishlist__user=request.user)
    wishlist_item.delete()
    messages.success(request, "Product removed from wishlist.")
    return redirect('wishlist')
@login_required
def wishlist_view(request):
    wishlists = Wishlist.objects.filter(user=request.user).prefetch_related(
        'items__variant__product', 
        'items__variant__images'
    )
    
    context = {
        'wishlists': wishlists,
        'wishlist_collections': wishlists, # Used for the "Move to" dropdown
    }
    return render(request,'customer_templates/wishlistpage.html',context)
def create_collection_view(request):
    if request.method == 'POST':
        wishlist_name = request.POST.get('collection_name')
        if wishlist_name:
            Wishlist.objects.create(user=request.user, wishlist_name=wishlist_name)
            messages.success(request, f"Collection '{wishlist_name}' created successfully.")
        else:
            messages.error(request, "Collection name cannot be empty.")
    return redirect('wishlist')
def update_collection_view(request):
    if request.method == 'POST':
        wishlist_id = request.POST.get('wishlist_id')
        wishlist_name = request.POST.get('collection_name')
        is_default_checked = (request.POST.get('is_default') == 'on')
        collection=get_object_or_404(Wishlist,id=wishlist_id,user=request.user)
        if collection.is_default and not is_default_checked:
            messages.error(request, "You cannot unset the default collection. Please set another collection as default first.")
            return redirect('wishlist')
        collection.wishlist_name=wishlist_name
        collection.is_default = is_default_checked
        collection.save()
        messages.success(request, f"Collection '{wishlist_name}' updated successfully.")
        return redirect('wishlist')
    else:
        messages.error(request, "Collection name cannot be empty.")
    return redirect('wishlist')
def delete_collection_view(request,wishlist_id):
    collection=get_object_or_404(Wishlist,id=wishlist_id,user=request.user)
    if collection.is_default:
        messages.error(request, "You cannot delete the default collection. Please set another collection as default first.")
        return redirect('wishlist')
    collection.delete()
    messages.success(request, f"Collection '{collection.wishlist_name}' deleted successfully.")
    return redirect('wishlist')
# ------------------------------------------------------------------------------

# customer dashboard-------------------------------------------------------------
def customer_dashboard_view(request):
    return render(request,'customer_templates/customer_dashboard.html')
def orderhistory_view(request):
    return render(request,'customer_templates/order_history_customer.html')
def address_view(request):
    return render(request,'customer_templates/addresspage.html')
def product_list_view(request):
    product_var=ProductVariant.objects.all()
    return render(request,'customer_templates/product_page.html',{"product_var":product_var})
def product_single_view(request):
    product_var=ProductVariant.objects.all()
    return render(request,'customer_templates/productsinglepage.html',{"product_var":product_var})
# Create your views here.
