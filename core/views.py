from django.shortcuts import render, redirect
from .models import CustomUser
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.decorators import admin_required, seller_required
from customer.models import Cart, CartItem
from .models import *
from seller.models import *
from django.db.models import Q, Count


def home_view(request):
    user = request.user
    category_items = Category.objects.all()
    product_var = (
        ProductVariant.objects.select_related("product__subcategory__category")
        .prefetch_related("images")
        .filter(product__approval_status="approved")
    )

    top_picks = (
        Product.objects.filter(approval_status="approved", is_active=True)
        .annotate(review_count=Count("review"))
        .select_related("subcategory__category")
        .prefetch_related("variants__images")
        .order_by("-review_count", "-created_at")[:12]
    )
    if user.is_authenticated and user.is_admin:
        return redirect(request.META.get("HTTP_REFERER", "admin_dashboard"))
    # if user.is_authenticated and user.role=="SELLER":
    #     return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    if user.is_authenticated:
        cart = Cart.objects.filter(user=user).first()
        cart_items = CartItem.objects.filter(cart=cart).prefetch_related(
            "variant__product__subcategory", "variant__images"
        )
        return render(
            request,
            "core_templates/homepage.html",
            {
                "user": user,
                "cart_items": cart_items,
                "categories": category_items,
                "product_var": product_var,
                "top_picks": top_picks,
            },
        )
    return render(
        request,
        "core_templates/homepage.html",
        {
            "categories": category_items,
            "product_var": product_var,
            "top_picks": top_picks,
        },
    )


# search-------------------------------------------------------------------------
def search_and_filter_view(request):
    query = request.GET.get("q", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    selected_categories = request.GET.getlist("category")
    selected_subcategory = request.GET.get("subcategory", "")
    sort_by = request.GET.get("sort", "featured")
    user = request.user

    if query:
        matched_variants = (
            ProductVariant.objects.filter(
                product__approval_status="approved", product__is_active=True
            )
            .filter(
                Q(product__name__icontains=query)
                | Q(product__description__icontains=query)
                | Q(product__subcategory__category__name__icontains=query)
            )
            .distinct()
        )
    elif selected_subcategory:
        matched_variants = ProductVariant.objects.filter(
            product__subcategory__slug=selected_subcategory,
            product__approval_status="approved",
            product__is_active=True,
        ).distinct()
    elif selected_categories:
        matched_variants = ProductVariant.objects.filter(
            product__approval_status="approved", product__is_active=True
        )
    elif min_price or max_price:
        matched_variants = ProductVariant.objects.filter(
            product__approval_status="approved", product__is_active=True
        )
    else:
        matched_variants = ProductVariant.objects.none()

    if selected_categories and "all" not in selected_categories:
        matched_variants = matched_variants.filter(
            product__subcategory__category__slug__in=selected_categories
        ).distinct()

    if min_price:
        try:
            min_price_val = float(min_price)
            matched_variants = matched_variants.filter(selling_price__gte=min_price_val)
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            max_price_val = float(max_price)
            matched_variants = matched_variants.filter(selling_price__lte=max_price_val)
        except (ValueError, TypeError):
            pass

    if sort_by == "price-low-high":
        matched_variants = matched_variants.order_by("selling_price")
    elif sort_by == "price-high-low":
        matched_variants = matched_variants.order_by("-selling_price")
    elif sort_by == "newest":
        matched_variants = matched_variants.order_by("-created_at")

    product_ids = matched_variants.values_list("product_id", flat=True).distinct()
    product_var = (
        Product.objects.filter(
            id__in=product_ids, approval_status="approved", is_active=True
        )
        .select_related("subcategory__category")
        .prefetch_related("variants__images")
    )

    if selected_categories and "all" not in selected_categories:
        product_var = product_var.filter(
            subcategory__category__slug__in=selected_categories
        ).distinct()

    # Price filtering using annotations since min/max_variant_price are properties (product-level)
    product_var = product_var.annotate(
        min_product_price=models.Min("variants__selling_price"),
        max_product_price=models.Max("variants__selling_price"),
    )

    if min_price:
        try:
            min_price_val = float(min_price)
            product_var = product_var.filter(min_product_price__gte=min_price_val)
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            max_price_val = float(max_price)
            product_var = product_var.filter(max_product_price__lte=max_price_val)
        except (ValueError, TypeError):
            pass

    # Sorting using annotations since min/max_variant_price are properties (product-level)
    if sort_by == "price-low-high":
        product_var = product_var.annotate(
            min_product_price=models.Min("variants__selling_price")
        ).order_by("min_product_price")
    elif sort_by == "price-high-low":
        product_var = product_var.annotate(
            max_product_price=models.Max("variants__selling_price")
        ).order_by("-max_product_price")
    elif sort_by == "newest":
        product_var = product_var.order_by("-created_at")

    categories = Category.objects.filter(is_active=True)
    wishlist_variant_ids = []
    cart_variant_ids = []
    cart_items = []

    if user.is_authenticated:
        from customer.models import WishlistItem, Cart, CartItem

        wishlist_variant_ids = list(
            WishlistItem.objects.filter(wishlist__user=user).values_list(
                "variant_id", flat=True
            )
        )
        cart = Cart.objects.filter(user=user).first()
        if cart:
            cart_items = CartItem.objects.filter(cart=cart).prefetch_related(
                "variant__product__subcategory", "variant__images"
            )
            cart_variant_ids = list(
                CartItem.objects.filter(cart=cart).values_list("variant_id", flat=True)
            )

    context = {
        "products": product_var,
        "product_var": product_var,
        "search_query": query,
        "cart_items": cart_items,
        "min_price": min_price,
        "max_price": max_price,
        "selected_categories": selected_categories,
        "selected_subcategory": selected_subcategory,
        "sort_by": sort_by,
        "categories": categories,
        "wishlist_variant_ids": wishlist_variant_ids,
        "cart_variant_ids": cart_variant_ids,
    }
    return render(request, "customer_templates/product_page.html", context)


# ------------------------------------------------------------------------------------


def category_list_view(request):
    categories = (
        Category.objects.filter(is_active=True)
        .prefetch_related("subcategories")
        .filter(subcategories__products__approval_status="approved")
        .distinct()
    )
    context = {"categories": categories}
    return render(request, "core_templates/categories.html", context)


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        if password != confirm_password:
            messages.error(request, "passwords doesnot match")
            return render(
                request,
                "core_templates/registerpage.html",
                {"username": username, "email": email},
            )
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Invalid username !")
            return render(
                request,
                "core_templates/registerpage.html",
                {"username": username, "email": email},
            )
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Invalid email !")
            return render(
                request,
                "core_templates/registerpage.html",
                {"username": username, "email": email},
            )

        user = CustomUser.objects.create_user(
            username=username, email=email, password=password
        )
        user.save()
        return redirect("login")
    return render(request, "core_templates/registerpage.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("usernameoremail")
        password = request.POST.get("password")
        try:
            user_obj = CustomUser.objects.get(email=username)
            username = user_obj.username
        except CustomUser.DoesNotExist:
            username = username
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "user successgully logined")
            if user.is_admin:
                return redirect("admin_dashboard")
            return redirect("home")
        else:
            messages.error(request, "invalid credintials !")
    return render(request, "core_templates/loginpage.html")


def logout_view(request):
    logout(request)
    return redirect("home")


def category_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = CartItem.objects.filter(cart=cart).prefetch_related(
        "variant__product__subcategory", "variant__images"
    )
    return render(request, "core_templates/categories.html", {"cart_items": cart_items})


def deals_view(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        cart_items = CartItem.objects.filter(cart=cart).prefetch_related(
            "variant__product__subcategory", "variant__images"
        )
    else:
        cart_items = []
    return render(request, "core_templates/dealspage.html", {"cart_items": cart_items})


# Create your views here.
