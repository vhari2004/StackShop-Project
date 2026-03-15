from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import customer_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Avg, Sum
from seller.models import Product, ProductVariant
from customer.models import (
    Wishlist,
    WishlistItem,
    Cart,
    CartItem,
    Order,
    PaymentOrder,
    OrderItem,
    Review,
)
from core.models import Address, Category
import razorpay
from django.conf import settings
from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import time
from django.views.decorators.http import require_http_methods


@csrf_exempt
def payment_success(request):

    data = json.loads(request.body)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    params_dict = {
        "razorpay_order_id": data["razorpay_order_id"],
        "razorpay_payment_id": data["razorpay_payment_id"],
        "razorpay_signature": data["razorpay_signature"],
    }

    try:
        client.utility.verify_payment_signature(params_dict)

        payment_order = PaymentOrder.objects.get(
            razorpay_order_id=data["razorpay_order_id"]
        )

        payment_order.razorpay_payment_id = data["razorpay_payment_id"]
        payment_order.razorpay_signature = data["razorpay_signature"]
        payment_order.status = "SUCCESS"
        payment_order.save()

        order = payment_order.order
        order.payment_status = "SUCCESS"
        order.order_status = "CONFIRMED"
        order.save()

        cart = Cart.objects.get(user=payment_order.user)
        cart_items = CartItem.objects.filter(cart=cart)

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                variant=cart_item.variant,
                seller=cart_item.variant.product.seller, 
                quantity=cart_item.quantity,
                price_at_purchase=cart_item.price_at_time,
            )

        cart_items.delete()

        return JsonResponse({"status": "payment verified"})

    except Exception as e:
        return JsonResponse({"status": "payment failed", "error": str(e)})


@login_required
def order_success(request):
    """Display order success page after payment completion"""
    try:
        payment_order = (
            PaymentOrder.objects.filter(user=request.user, status="SUCCESS")
            .order_by("-created_at")
            .first()
        )

        if payment_order:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()

            context = {
                "order": payment_order.order,
                "payment_order": payment_order,
                "order_amount": payment_order.amount
                / 100, 
            }
            return render(request, "customer_templates/order_success.html", context)
        else:
            messages.error(request, "No order found.")
            return redirect("cart_view")
    except Cart.DoesNotExist:
        messages.error(request, "Cart not found.")
        return redirect("cart_view")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect("cart_view")


# userlogin-----------------------------------------------------------------------------


@customer_required
def user_profile_view(request):
    user = request.user
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone = request.POST.get("phone")
        image = request.FILES.get("profile_photo")
        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone
        if image:
            user.profile_image = image
        user.save()
    return render(request, "customer_templates/profile.html", {"user": user})


# ------------------------------------------------------------------------------

# wishlist---------------------------------------------------------------------


@require_http_methods(["POST"])
@login_required
@csrf_protect
def toggle_wishlist_view(request, product_id):
    """AJAX endpoint to toggle product in user's default wishlist"""
    try:
        product = get_object_or_404(Product, id=product_id, approval_status="approved", is_active=True)
        
        # Get user's default wishlist
        try:
            wishlist = Wishlist.objects.get(user=request.user, is_default=True)
        except Wishlist.DoesNotExist:
            wishlist = Wishlist.objects.create(
                user=request.user,
                wishlist_name=f"{request.user.username}'s Favorites",
                is_default=True
            )
        
        # Check if any variant of this product is in wishlist
        existing_item = WishlistItem.objects.filter(
            wishlist=wishlist, 
            variant__product=product
        ).first()
        
        if existing_item:
            # Remove from wishlist
            existing_item.delete()
            return JsonResponse({
                "success": True, 
                "message": "Removed from wishlist",
                "in_wishlist": False
            })
        else:
            # Add first available variant to wishlist
            variant = product.variants.filter(stock_quantity__gt=0).first()
            if variant:
                WishlistItem.objects.create(wishlist=wishlist, variant=variant)
                return JsonResponse({
                    "success": True, 
                    "message": "Added to wishlist",
                    "in_wishlist": True
                })
            else:
                return JsonResponse({
                    "success": False, 
                    "message": "No available variants in stock"
                })
                
    except Product.DoesNotExist:
        return JsonResponse({"success": False, "message": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@customer_required
def add_wishlist_view(request, variant_id):
    product_variant = get_object_or_404(ProductVariant, id=variant_id)
    try:
        wishlist = Wishlist.objects.get(user=request.user, is_default=True)
    except Wishlist.DoesNotExist:
        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            wishlist_name=f"{request.user.username}'s Wishlist",
            is_default=True,
        )
        if created:
            messages.success(request, f"( {wishlist.wishlist_name} ) created.")

    wishlist_item = WishlistItem.objects.filter(
        wishlist=wishlist, variant=product_variant
    )
    if wishlist_item.exists():
        wishlist_item.delete()
        messages.warning(request, f"Product removed from ( {wishlist.wishlist_name} ).")
    else:
        WishlistItem.objects.create(wishlist=wishlist, variant=product_variant)
        messages.success(request, f"Product added to ( {wishlist.wishlist_name} ).")

    return redirect(request.META.get("HTTP_REFERER", "home"))


@customer_required
def remove_wishlist_view(request, wishlist_item_id):
    wishlist_item = get_object_or_404(WishlistItem, id=wishlist_item_id, wishlist__user=request.user)
    wishlist_item.delete()
    messages.success(request, "Product removed from wishlist.")
    return redirect("wishlist")


@customer_required
def wishlist_view(request):
    wishlists = (
        Wishlist.objects.filter(user=request.user)
        .prefetch_related(
            "items__variant__product__subcategory", "items__variant__images"
        )
        .order_by("-is_default", "-created_at")
    )

    paginator = Paginator(wishlists, settings.PAGINATE_BY)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "wishlists": page_obj,
        "wishlist_collections": wishlists,
    }
    return render(request, "customer_templates/wishlistpage.html", context)

@customer_required
def create_collection_view(request):
    if request.method == "POST":
        wishlist_name = request.POST.get("collection_name")
        if wishlist_name:
            Wishlist.objects.create(user=request.user, wishlist_name=wishlist_name)
            messages.success(
                request, f"Collection '{wishlist_name}' created successfully."
            )
        else:
            messages.error(request, "Collection name cannot be empty.")
    return redirect("wishlist")

@customer_required
def update_collection_view(request):
    if request.method == "POST":
        wishlist_id = request.POST.get("wishlist_id")
        wishlist_name = request.POST.get("collection_name")
        is_default_checked = request.POST.get("is_default") == "on"
        collection = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
        if collection.is_default and not is_default_checked:
            messages.error(
                request,
                "You cannot unset the default collection. Please set another collection as default first.",
            )
            return redirect("wishlist")
        collection.wishlist_name = wishlist_name
        collection.is_default = is_default_checked
        collection.save()
        messages.success(request, f"Collection '{wishlist_name}' updated successfully.")
        return redirect("wishlist")
    else:
        messages.error(request, "Collection name cannot be empty.")
    return redirect("wishlist")

@customer_required
def delete_collection_view(request, wishlist_id):
    collection = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    if collection.is_default:
        messages.error(
            request,
            "You cannot delete the default collection. Please set another collection as default first.",
        )
        return redirect("wishlist")
    collection.delete()
    messages.success(
        request, f"Collection '{collection.wishlist_name}' deleted successfully."
    )
    return redirect("wishlist")


# ------------------------------------------------------------------------------

# cart---------------------------------------------------------------------------
@customer_required
def add_to_cart_view(request, variant_id):
    user = request.user
    product_variant = get_object_or_404(ProductVariant, id=variant_id)
    cart, _ = Cart.objects.get_or_create(user=user)

    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1

    max_allowed = min(3, product_variant.stock_quantity)
    if quantity > max_allowed:
        quantity = max_allowed
        messages.warning(request, "Quantity per product is limited to 3 units.")

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        variant=product_variant,
        defaults={"quantity": quantity, "price_at_time": product_variant.selling_price},
    )
    if not created:
        new_quantity = min(cart_item.quantity + quantity, max_allowed)
        if new_quantity == cart_item.quantity:
            messages.warning(request, "Each product can have a maximum of 3 units in the cart.")
        else:
            cart_item.quantity = new_quantity
            cart_item.price_at_time = product_variant.selling_price
            cart_item.save()
    messages.success(request, f"{product_variant.product.name} added to cart.")
    return redirect(request.META.get("HTTP_REFERER", "product_list"))


@customer_required
def buy_now_view(request, variant_id):
    """Adds product to cart and redirects directly to checkout"""
    user = request.user
    product_variant = get_object_or_404(ProductVariant, id=variant_id)
    cart, _ = Cart.objects.get_or_create(user=user)

    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1

    max_allowed = min(3, product_variant.stock_quantity)
    if quantity > max_allowed:
        quantity = max_allowed
        messages.warning(request, "Quantity per product is limited to 3 units.")

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        variant=product_variant,
        defaults={"quantity": quantity, "price_at_time": product_variant.selling_price},
    )
    if not created:
        new_quantity = min(cart_item.quantity + quantity, max_allowed)
        if new_quantity == cart_item.quantity:
            messages.warning(request, "Each product can have a maximum of 3 units in the cart.")
        else:
            cart_item.quantity = new_quantity
            cart_item.price_at_time = product_variant.selling_price
            cart_item.save()
    
    messages.success(request, f"{product_variant.product.name} added to cart. Proceeding to checkout...")
    return redirect("checkout")


@customer_required
def cart_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).prefetch_related(
        "variant__product__subcategory", "variant__images"
    )
    cart_total = sum(item.get_total() for item in cart_items)
    tax_amount = cart_total * 0.18
    total_amount = cart_total + tax_amount
    return render(
        request,
        "customer_templates/cartpage.html",
        {
            "cart_items": cart_items,
            "cart_total": cart_total,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
        },
    )


@customer_required
def update_cart_view(request, cart_item_id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
        action = request.POST.get("action")
        if action == "increase":
            max_allowed = min(3, cart_item.variant.stock_quantity)
            if cart_item.quantity < max_allowed:
                cart_item.quantity += 1
                cart_item.price_at_time = cart_item.variant.selling_price
                cart_item.save()
            else:
                messages.warning(request, "Each product can have a maximum of 3 units in the cart.")
        elif action == "decrease":
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.price_at_time = cart_item.variant.selling_price
                cart_item.save()
            else:
                cart_item.delete()
    return redirect("cart_view")


@customer_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).prefetch_related(
        "variant__product__subcategory", "variant__images"
    )

    # Get user's addresses
    user_addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    default_address = user_addresses.filter(is_default=True).first()

    cart_total = sum(item.get_total() for item in cart_items)
    tax_amount = cart_total * 0.18
    total_amount = cart_total + tax_amount

    amount_in_paise = int(total_amount * 100)

    # Get selected address ID from POST request or use default
    selected_address_id = request.POST.get('address_id')
    if selected_address_id:
        selected_address = user_addresses.filter(id=selected_address_id).first()
    else:
        selected_address = default_address

    try:
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        payment = client.order.create(
            {
                "amount": amount_in_paise,
                "currency": "INR",
                "payment_capture": "1",
                "receipt": f"order_{request.user.id}_{int(time.time())}",
            }
        )

        order_obj = Order.objects.create(
            user=request.user,
            address=selected_address,
            order_number=f"ORD-{request.user.id}-{int(time.time())}",
            total_amount=total_amount,
            payment_status="PENDING",
            order_status="PENDING",
        )

        payment_order = PaymentOrder.objects.create(
            order=order_obj,
            amount=amount_in_paise,
            razorpay_order_id=payment["id"],
            user=request.user,
            status="PENDING",
        )

        context = {
            "cart_items": cart_items,
            "cart_total": cart_total,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "payment": payment,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "user_addresses": user_addresses,
            "default_address": default_address,
            "selected_address": selected_address,
        }
    except Exception as e:
        messages.error(request, f"Payment initialization failed: {str(e)}")
        context = {
            "cart_items": cart_items,
            "cart_total": cart_total,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "error": str(e),
            "user_addresses": user_addresses,
            "default_address": default_address,
            "selected_address": selected_address,
        }

    return render(request, "customer_templates/checkout.html", context)


@customer_required
def remove_from_cart_view(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Product removed from cart.")
    return redirect("cart_view")


# -----------------------------------------------------------------------------
# address----------------------------------------------------------------------
@customer_required
def add_address_view(request):
    if request.method == "POST":
        has_addresses = Address.objects.filter(user=request.user).exists()
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        full_name = f"{first_name} {last_name}"
        phone_number = request.POST.get("phone_number")
        locality = request.POST.get("locality")
        city = request.POST.get("city")
        state = request.POST.get("state")
        pincode = request.POST.get("pincode")
        country = request.POST.get("country")
        house_info = request.POST.get("house_info")
        landmark = request.POST.get("landmark")
        address_type = request.POST.get("address_type")
        is_default_checked = request.POST.get("is_default") == "on"

        if not has_addresses:
            is_default_checked = True

        if is_default_checked:
            Address.objects.filter(user=request.user, is_default=True).update(
                is_default=False
            )

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
            is_default=is_default_checked,
        )
        messages.success(request, "Address added successfully.")
        return redirect("address")
    return redirect("address")


@customer_required
def address_view(request):
    user_address = Address.objects.filter(user=request.user).order_by(
        "-is_default", "-created_at"
    )
    return render(
        request, "customer_templates/addresspage.html", {"addresses": user_address}
    )


@customer_required
def update_address_view(request):
    if request.method == "POST":
        address_id = request.POST.get("address_id")
        address = get_object_or_404(Address, id=address_id, user=request.user)
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        is_default_checked = request.POST.get("is_default") == "on"
        if address.is_default and not is_default_checked:
            messages.error(
                request,
                "You cannot unset your default address directly. Please set another address as default instead.",
            )
            return redirect("address")
        if is_default_checked and not address.is_default:
            Address.objects.filter(user=request.user, is_default=True).update(
                is_default=False
            )
        address.full_name = full_name
        address.phone_number = request.POST.get("phone_number")
        address.locality = request.POST.get("locality")
        address.city = request.POST.get("city")
        address.state = request.POST.get("state")
        address.pincode = request.POST.get("pincode")
        address.country = request.POST.get("country")
        address.house_info = request.POST.get("house_info")
        address.landmark = request.POST.get("landmark", "")
        address.address_type = request.POST.get("address_type")
        address.is_default = is_default_checked
        address.save()
        messages.success(request, f"Address updated successfully.")
        return redirect("address")
    return redirect("address")


@customer_required
def delete_address_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, "Address deleted successfully.")
    return redirect("address")


@customer_required
def set_default_address_view(request):
    if request.method == "POST":
        address_id = request.POST.get("address_id")
        if address_id:
            address = get_object_or_404(Address, id=address_id, user=request.user)
            Address.objects.filter(user=request.user, is_default=True).update(
                is_default=False
            )
            address.is_default = True
            address.save()
            messages.success(request, "Default address set successfully.")
        else:
            messages.error(request, "No address selected to set as default.")
    return redirect("address")


# ------------------------------------------------------------------------------

# product_view_user-------------------------------------------------------------------
def product_list_view(request):
    products_all = (
        Product.objects.filter(approval_status="approved", is_active=True)
        .select_related("subcategory__category", "seller")
        .prefetch_related("variants__images")
    )
    categories = Category.objects.all()

    paginator = Paginator(products_all, settings.PAGINATE_BY)
    page_number = request.GET.get("page", 1)

    try:
        products_page = paginator.page(page_number)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    # Add is_in_wishlist for logged-in users
    if request.user.is_authenticated:
        try:
            default_wishlist = Wishlist.objects.get(user=request.user, is_default=True)
            wishlist_variant_ids = set(WishlistItem.objects.filter(wishlist=default_wishlist).values_list('variant__product_id', flat=True))
        except Wishlist.DoesNotExist:
            wishlist_variant_ids = set()
    else:
        wishlist_variant_ids = set()

    for product in products_page:
        product.is_in_wishlist = product.id in wishlist_variant_ids

    return render(
        request,
        "customer_templates/product_page.html",
        {
            "products": products_page,
            "categories": categories,
            "paginator": paginator,
            "page_obj": products_page,
        },
    )


def product_single_view(request, product_slug=None, product_id=None):
    lookup = {}
    if product_slug:
        lookup["slug"] = product_slug
    elif product_id:
        lookup["id"] = product_id
    else:
        return redirect("product_list")

    product = get_object_or_404(
        Product.objects.select_related("subcategory__category", "seller")
        .prefetch_related("variants__images", "variants__attributes__option__attribute"),
        approval_status="approved",
        is_active=True,
        **lookup,
    )

    variants = product.variants.all().order_by("id")
    selected_variant = None

    variant_id = request.GET.get("variant")
    if variant_id:
        selected_variant = variants.filter(id=variant_id).first()

    if not selected_variant:
        selected_variant = variants.first()

    if not selected_variant:
        messages.error(request, "No available variant for this product.")
        return redirect("product_list")

    for v in variants:
        option_descs = []
        for brid in v.attributes.select_related("option__attribute").all():
            option_descs.append(f"{brid.option.attribute.name}: {brid.option.value}")
        v.variant_label = ", ".join(sorted(option_descs)) if option_descs else "Default"

    reviews = Review.objects.filter(product=product).select_related("user").order_by("-created_at")
    average_rating = reviews.aggregate(avg=Avg("rating"))["avg"] or 0
    total_reviews = reviews.count()

    has_purchased = Review.can_user_review(request.user, product)
    user_review = Review.get_user_review(request.user, product)

    cart_items = []
    wishlist_variant_ids = []
    cart_variant_ids = []

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_items = CartItem.objects.filter(cart=cart).prefetch_related(
                "variant__product__subcategory", "variant__images"
            )
            cart_variant_ids = list(
                CartItem.objects.filter(cart=cart).values_list("variant_id", flat=True)
            )

        wishlist_variant_ids = list(
            WishlistItem.objects.filter(wishlist__user=request.user).values_list(
                "variant_id", flat=True
            )
        )

    return render(
        request,
        "customer_templates/productsinglepage.html",
        {
            "product": product,
            "variant": selected_variant,
            "variants": variants,
            "cart_items": cart_items,
            "wishlist_variant_ids": wishlist_variant_ids,
            "cart_variant_ids": cart_variant_ids,
            "category": Category.objects.all(),
            "reviews": reviews,
            "average_rating": round(average_rating, 1),
            "total_reviews": total_reviews,
            "has_purchased": has_purchased,
            "user_review": user_review,
        },
    )


def product_single_view_by_id(request, product_id):
    return product_single_view(request, product_id=product_id)


@login_required
def submit_review(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product

    if not OrderItem.objects.filter(order__user=request.user, variant__product=product, order__payment_status__in=["SUCCESS", "CONFIRMED", "DELIVERED"]).exists():
        messages.error(request, "Only verified buyers can add reviews.")
        return redirect("productsingle", product_slug=product.slug)

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "").strip()

        if not rating or not comment:
            messages.error(request, "Rating and comment are required.")
            return redirect("productsingle", product_slug=product.slug)

        try:
            rating_value = int(rating)
            if rating_value < 1 or rating_value > 5:
                raise ValueError
        except ValueError:
            messages.error(request, "Invalid rating value.")
            return redirect("productsingle", product_slug=product.slug)

        Review.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={"rating": rating_value, "comment": comment},
        )

        messages.success(request, "Thank you! Your review has been submitted.")

    return redirect("productsingle", product_slug=product.slug)


# ----------------------------------------------------------------------------------------------------

# order---------------------------------------------------------------------------
@customer_required
def order_history_view(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__variant__product", "items__variant__images")
        .order_by("-ordered_at")
    )

    paginator = Paginator(orders, settings.PAGINATE_BY)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "orders": page_obj,
    }
    return render(request, "customer_templates/order_history_customer.html", context)


@customer_required
def my_reviews_view(request):
    reviews = (
        Review.objects.filter(user=request.user)
        .select_related("product", "product__seller")
        .order_by("-created_at")
    )

    from django.core.paginator import Paginator
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "customer_templates/my_reviews.html",
        {
            "page_obj": page_obj,
        },
    )


# --------------------------------------------------------------------------------

# customer dashboard-------------------------------------------------------------
@customer_required
def customer_dashboard_view(request):
    orders = Order.objects.filter(user=request.user)

    total_orders = orders.count()
    total_spent_value = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    in_transit = orders.filter(order_status__in=['pending', 'processing']).count()

    user_reviews = Review.objects.filter(user=request.user).select_related('product').order_by('-created_at')
    total_reviews = user_reviews.count()
    recent_reviews = user_reviews[:2]

    context = {
        'total_orders': total_orders,
        'total_spent': total_spent_value,
        'in_transit': in_transit,
        'total_reviews': total_reviews,
        'recent_reviews': recent_reviews,
    }

    return render(request, 'customer_templates/customer_dashboard.html', context)


# ----------------------------------------------------------------------------------

# Create your views here.
