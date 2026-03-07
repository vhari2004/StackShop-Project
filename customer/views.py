from urllib import request
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from seller.models import Product,ProductVariant
from customer.models import Wishlist,WishlistItem,Cart,CartItem
from core.models import *
from django.contrib import messages
from core.models import Address
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
    
    # Toggle: remove if exists, add if doesn't exist
    wishlist_item = WishlistItem.objects.filter(wishlist=wishlist, variant=product_variant)
    if wishlist_item.exists():
        wishlist_item.delete()
        messages.warning(request, f"Product removed from ( {wishlist.wishlist_name} ).")
    else:
        WishlistItem.objects.create(wishlist=wishlist, variant=product_variant)
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
    wishlists = Wishlist.objects.filter(user=request.user).prefetch_related('items__variant__product__subcategory', 'items__variant__images').order_by('-is_default', '-created_at')
    context = {
        'wishlists': wishlists,'wishlist_collections': wishlists, 
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

#cart---------------------------------------------------------------------------
@login_required
def add_to_cart_view(request,id):
    user=request.user
    product_variant=get_object_or_404(ProductVariant,id=id)
    cart, _ = Cart.objects.get_or_create(user=user)
    cart_item,created=CartItem.objects.get_or_create(cart=cart,variant=product_variant,defaults={'quantity': 1, 'price_at_time': product_variant.selling_price})
    if not created:
        cart_item.quantity += 1
        cart_item.price_at_time = product_variant.selling_price
        cart_item.save()
    messages.success(request, f"{product_variant.product.name} added to cart.")
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))
@login_required
def cart_view(request):
    cart=get_object_or_404(Cart, user=request.user)
    cart_items=CartItem.objects.filter(cart=cart).prefetch_related('variant__product__subcategory','variant__images')
    cart_total = sum(item.get_total() for item in cart_items)        
    tax_amount = cart_total * 0.18
    total_amount = cart_total + tax_amount
    return render(request,'customer_templates/cartpage.html',{'cart_items': cart_items,'cart_total': cart_total,'tax_amount': tax_amount,'total_amount': total_amount})

@login_required
def update_cart_view(request,id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=id, cart__user=request.user)
        action = request.POST.get('action')
        if action=="increase":
            cart_item.quantity += 1
            cart_item.price_at_time = cart_item.variant.selling_price
            cart_item.save()
        elif action=="decrease":
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.price_at_time = cart_item.variant.selling_price
                cart_item.save()
            else:
                cart_item.delete()
    return redirect('cart_view')

@login_required
def checkout_view(request):
    cart=get_object_or_404(Cart, user=request.user)
    cart_items=CartItem.objects.filter(cart=cart).prefetch_related('variant__product__subcategory','variant__images')
    context={'cart_items':cart_items}
    return render(request,'customer_templates/checkout.html',context)

@login_required
def remove_from_cart_view(request, id):
    cart_item=get_object_or_404(CartItem, id=id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Product removed from cart.")
    return redirect('cart_view')
    
@login_required
def checkout_view(request):
    return render(request,'customer_templates/checkout.html')
#-----------------------------------------------------------------------------
#address----------------------------------------------------------------------
@login_required
def add_address_view(request):
    if request.method == 'POST':
        has_addresses = Address.objects.filter(user=request.user).exists()
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        full_name = f"{first_name} {last_name}"
        phone_number = request.POST.get('phone_number')
        locality = request.POST.get('locality')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        country = request.POST.get('country')
        house_info = request.POST.get('house_info')
        landmark = request.POST.get('landmark')
        address_type = request.POST.get('address_type')
        is_default_checked = request.POST.get('is_default') == 'on'

        if not has_addresses:
            is_default_checked = True

        if is_default_checked:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone_number=phone_number,
            locality=locality,
            city=city,
            state=state,
            pincode=pincode,
            country=country,
            house_info=house_info,
            landmark=landmark,
            address_type=address_type,
            is_default=is_default_checked
        )
        messages.success(request, "Address added successfully.")
        return redirect('address')
    return redirect('address')

@login_required
def address_view(request):
    user_address = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return render(request,'customer_templates/addresspage.html',{'addresses': user_address})

@login_required
def update_address_view(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        address = get_object_or_404(Address, id=address_id, user=request.user)
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        is_default_checked = request.POST.get('is_default') == 'on'
        if address.is_default and not is_default_checked:
            messages.error(request, "You cannot unset your default address directly. Please set another address as default instead.")
            return redirect('address')
        if is_default_checked and not address.is_default:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        address.full_name = full_name
        address.phone_number = request.POST.get('phone_number')
        address.locality = request.POST.get('locality')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.pincode = request.POST.get('pincode')
        address.country = request.POST.get('country')
        address.house_info = request.POST.get('house_info')
        address.landmark = request.POST.get('landmark', '')
        address.address_type = request.POST.get('address_type')
        address.is_default = is_default_checked
        address.save()
        messages.success(request, f"Address updated successfully.")
        return redirect('address')
    return redirect('address')
@login_required
def delete_address_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, "Address deleted successfully.")
    return redirect('address')
@login_required
def set_default_address_view(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if address_id:
            address = get_object_or_404(Address, id=address_id, user=request.user)
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            address.is_default = True
            address.save()
            messages.success(request, "Default address set successfully.")
        else:
            messages.error(request, "No address selected to set as default.")
    return redirect('address')
#------------------------------------------------------------------------------

#product_view_user-------------------------------------------------------------------
def product_list_view(request):
    product_var = ProductVariant.objects.select_related('product__subcategory__category').prefetch_related('images').all()
    categories=Category.objects.all()
    cart_variant_ids = []
    wishlist_variant_ids = []
    
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart_items = CartItem.objects.filter(cart=cart).prefetch_related('variant__product__subcategory', 'variant__images')
                cart_variant_ids = list(cart_items.values_list('variant_id', flat=True))
            
            wishlist = Wishlist.objects.filter(user=request.user, is_default=True).first()
            if wishlist:
                wishlist_items = WishlistItem.objects.filter(wishlist=wishlist).prefetch_related('variant__product__subcategory', 'variant__images')
                wishlist_variant_ids = list(wishlist_items.values_list('variant_id', flat=True))
            
            return render(request, 'customer_templates/product_page.html', {
                "product_var": product_var,
                "cart_variant_ids": cart_variant_ids,
                "wishlist_variant_ids": wishlist_variant_ids,
                'categories':categories
            })
    except:
        return redirect('login')
    
    return render(request, 'customer_templates/product_page.html', {
        "product_var": product_var,
        "cart_variant_ids": cart_variant_ids,
        "wishlist_variant_ids": wishlist_variant_ids,
        'categories':categories
    })
def product_single_view(request,id):
    product_var=ProductVariant.objects.select_related('product__subcategory__category').prefetch_related('images').get(id=id)
    cart=Cart.objects.filter(user=request.user).first()
    cart_items=CartItem.objects.filter(cart=cart).prefetch_related('variant__product__subcategory','variant__images')
    return render(request,'customer_templates/productsinglepage.html',{"variant":product_var,"cart_items":cart_items})
#----------------------------------------------------------------------------------------------------

#order---------------------------------------------------------------------------
def orderhistory_view(request):
    
    return render(request,'customer_templates/order_history_customer.html')
#--------------------------------------------------------------------------------

# customer dashboard-------------------------------------------------------------
def customer_dashboard_view(request):
    return render(request,'customer_templates/customer_dashboard.html')
#----------------------------------------------------------------------------------

# Create your views here.
