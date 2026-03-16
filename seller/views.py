from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from core.decorators import seller_required, verified_seller_required
from .models import (
    SellerProfile,
    Product,
    SubCategory,
    Attribute,
    VariantAttributeBridge,
    ProductVariant,
    ProductImage,
)
from core.models import *
from core.models import Category
from django.db.models import Count, Avg, Max, Sum, Q
from customer.models import Order, OrderItem, Review
from django.contrib import messages
import random


@login_required
@seller_required
def seller_profile_view(request):
    profile, _ = SellerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":

        profile.store_name = request.POST.get("store_name")
        profile.store_slug = request.POST.get("store_slug")
        profile.gst_number = request.POST.get("gst_number")
        profile.pan_number = request.POST.get("pan_number")
        profile.bank_account_number = request.POST.get("bank_account_number")
        profile.ifsc_code = request.POST.get("ifsc_code")
        profile.business_address = request.POST.get("business_address")

        if request.FILES.get("store_image"):
            profile.store_image = request.FILES.get("store_image")

        profile.save()
        return redirect("dashboard")

    return render(
        request, "seller_templates/sellerprofilepage.html", {"profile": profile}
    )


@verified_seller_required
def dashboard_view(request):
    seller = request.user.seller_profile
    products = Product.objects.filter(seller=seller).order_by("-id")

    total_products = products.count()

    active_orders = (
        OrderItem.objects.filter(seller=seller)
        .exclude(status__in=["delivered", "cancelled"])
        .count()
    )

    needs_shipping = OrderItem.objects.filter(
        seller=seller, status__in=["pending", "processing"]
    ).count()

    total_reviews = Review.objects.filter(product__seller=seller).count()
    avg_rating = (
        Review.objects.filter(product__seller=seller)
        .aggregate(avg=Avg("rating"))
        .get("avg")
        or 0
    )
    avg_rating = round(avg_rating, 1)

    total_orders = (
        OrderItem.objects.filter(seller=seller).values("order_id").distinct().count()
    )
    pending_actions = (
        OrderItem.objects.filter(seller=seller, status__in=["pending", "processing"])
        .values("order_id")
        .distinct()
        .count()
    )
    revenue_from_completed = (
        OrderItem.objects.filter(seller=seller, status="delivered").aggregate(
            total=Sum("price_at_purchase")
        )["total"]
        or 0
    )

    context = {
        "products": products,
        "total_products": total_products,
        "active_orders": active_orders,
        "needs_shipping": needs_shipping,
        "average_rating": avg_rating,
        "total_reviews": total_reviews,
        "total_orders": total_orders,
        "pending_actions": pending_actions,
        "total_revenue": revenue_from_completed,
    }

    return render(request, "seller_templates/sellerdashboard.html", context)


def seller_bridge(request):
    role = request.GET.get("role")
    if (
        request.user.is_authenticated
        and SellerProfile.objects.filter(user=request.user).exists()
    ):
        return redirect("seller-profile")
    if request.method == "POST":
        if request.user.is_authenticated and request.method == "POST":
            seller_profile, created = SellerProfile.objects.get_or_create(
                user=request.user
            )
            seller_profile.store_name = request.POST.get("store_name")
            seller_profile.gst_number = request.POST.get("tax_id", "")
            seller_profile.pan_number = request.POST.get("pan_number", "")
            seller_profile.bank_account_number = request.POST.get(
                "bank_account_number", ""
            )
            seller_profile.ifsc_code = request.POST.get("ifsc_code", "")
            seller_profile.business_address = request.POST.get("description", "")

            if request.FILES.get("logo"):
                seller_profile.store_image = request.FILES.get("logo")

            seller_profile.save()

            user = request.user
            user.is_seller = True
            user.save()
            user.refresh_from_db()

            return redirect("seller-profile")
        else:
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            # if first_name and last_name:
            #     username=first_name+last_name
            #     if CustomUser.objects.get(username=username).exist():
            #         return render(request,"seller_templates/seller_bridge.html",{"error": "username already exist"},)
            #     else:
            #         username = first_name + last_name + str(random.randint(1000, 9999))
            username = request.POST.get("username")
            email = request.POST.get("email")
            phone_number = request.POST.get("phone_number")
            password = request.POST.get("password")
            cnf_password = request.POST.get("password")
            if password != cnf_password:
                return render(
                    request,
                    "seller_templates/seller_bridge.html",
                    {"error": "Passwords do not match"},
                )
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, "Username already exists!")
                return render(
                    request,
                    "seller_templates/seller_bridge",
                    {"username": username, "email": email},
                )
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email already exists!")
                return render(
                    request,
                    "seller_templates/seller_bridge",
                    {"username": username, "email": email},
                )
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                phone_number=phone_number,
                role="SELLER",
                is_seller=True,
            )
            SellerProfile.objects.create(
                user=user,
                store_name=request.POST.get("store_name"),
                business_address=request.POST.get("business_address"),
                gst_number=request.POST.get("gst_no"),
                description=request.POST.get("description"),
                pan_number=request.POST.get("pan_no"),
                bank_account_number=request.POST.get("bank_account_number"),
                ifsc_code=request.POST.get("ifsc_code"),
                store_image=request.FILES.get("logo"),
            )
        redirect("login")
    return render(request, "seller_templates/seller_bridge.html")


def seller_broche_view(request):
    if request.user.is_authenticated:
        if (
            SellerProfile.objects.filter(user=request.user).exists()
            and request.user.is_seller
            and request.user.is_verified_seller
        ):
            return redirect("dashboard")
        elif (
            SellerProfile.objects.filter(user=request.user).exists()
            and request.user.is_seller
        ):
            return redirect("seller-profile")
        else:
            return redirect("seller-bridge")
    return render(request, "seller_templates/seller_broche.html")


@verified_seller_required
def add_product(request):
    seller = request.user.seller_profile
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    attributes = Attribute.objects.prefetch_related("options").all()

    if request.method == "POST":

        product = Product.objects.create(
            seller=seller,
            subcategory_id=request.POST.get("subcategory"),
            name=request.POST.get("name"),
            description=request.POST.get("description"),
            brand=request.POST.get("brand"),
            model_number=request.POST.get("model_number"),
        )

        variant = ProductVariant.objects.create(
            product=product,
            mrp=request.POST.get("mrp") or 0,
            selling_price=request.POST.get("selling_price") or 0,
            cost_price=request.POST.get("cost_price") or 0,
            stock_quantity=request.POST.get("stock_quantity") or 0,
            weight=request.POST.get("weight") or 0,
            length=request.POST.get("length") or 0,
            width=request.POST.get("width") or 0,
            height=request.POST.get("height") or 0,
            tax_percentage=request.POST.get("tax_percentage") or 0,
        )

        for attribute in attributes:
            option_id = request.POST.get(f"attribute_{attribute.id}")
            if option_id:
                VariantAttributeBridge.objects.create(
                    variant=variant, option_id=option_id
                )
        primary_image = request.FILES.get("primary_image")
        if primary_image:
            ProductImage.objects.create(
                variant=variant, image_url=primary_image, is_primary=True
            )

        additional_images = request.FILES.getlist("additional_images")
        for image in additional_images:
            ProductImage.objects.create(
                variant=variant, image_url=image, is_primary=False
            )

        return redirect("dashboard")
    context = {
        "categories": categories,
        "subcategories": subcategories,
        "attributes": attributes,
    }
    return render(request, "seller_templates/add_product.html", context)


@verified_seller_required
def update_product(request, product_slug):
    seller = request.user.seller_profile
    product = get_object_or_404(Product, slug=product_slug, seller=seller)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.brand = request.POST.get("brand")
        product.save()
        return redirect("dashboard")

    return render(request, "seller_templates/update_product.html", {"product": product})


@verified_seller_required
def manage_variants(request, product_slug):
    seller = request.user.seller_profile
    product = get_object_or_404(Product, slug=product_slug, seller=seller)
    attributes = Attribute.objects.filter(
        subcategory=product.subcategory
    ).prefetch_related("options")
    variants = product.variants.prefetch_related(
        "images", "attributes__option__attribute"
    )

    edit_variant = None
    selected_option_ids = []

    if request.method == "POST":
        edit_variant_id = request.POST.get("edit_variant_id")
        if edit_variant_id:
            variant = get_object_or_404(
                ProductVariant, id=edit_variant_id, product=product
            )
            variant.mrp = request.POST.get("mrp") or 0
            variant.selling_price = request.POST.get("selling_price") or 0
            variant.cost_price = request.POST.get("cost_price") or 0
            variant.stock_quantity = request.POST.get("stock_quantity") or 0
            variant.weight = request.POST.get("weight") or 0
            variant.length = request.POST.get("length") or 0
            variant.width = request.POST.get("width") or 0
            variant.height = request.POST.get("height") or 0
            variant.tax_percentage = request.POST.get("tax_percentage") or 0
            variant.save()

            VariantAttributeBridge.objects.filter(variant=variant).delete()
            for attribute in attributes:
                option_id = request.POST.get(f"attribute_{attribute.id}")
                if option_id:
                    VariantAttributeBridge.objects.create(
                        variant=variant, option_id=option_id
                    )

            primary_image = request.FILES.get("primary_image")
            if primary_image:
                ProductImage.objects.filter(variant=variant, is_primary=True).delete()
                ProductImage.objects.create(
                    variant=variant, image_url=primary_image, is_primary=True
                )

            additional_images = request.FILES.getlist("additional_images")
            for image in additional_images:
                ProductImage.objects.create(
                    variant=variant, image_url=image, is_primary=False
                )

            messages.success(request, "Variant updated successfully.")
            return redirect("manage_variants", product_slug=product.slug)

        # new variant create
        variant = ProductVariant.objects.create(
            product=product,
            mrp=request.POST.get("mrp") or 0,
            selling_price=request.POST.get("selling_price") or 0,
            cost_price=request.POST.get("cost_price") or 0,
            stock_quantity=request.POST.get("stock_quantity") or 0,
            weight=request.POST.get("weight") or 0,
            length=request.POST.get("length") or 0,
            width=request.POST.get("width") or 0,
            height=request.POST.get("height") or 0,
            tax_percentage=request.POST.get("tax_percentage") or 0,
        )

        for attribute in attributes:
            option_id = request.POST.get(f"attribute_{attribute.id}")
            if option_id:
                VariantAttributeBridge.objects.create(
                    variant=variant, option_id=option_id
                )

        primary_image = request.FILES.get("primary_image")
        if primary_image:
            ProductImage.objects.create(
                variant=variant, image_url=primary_image, is_primary=True
            )

        additional_images = request.FILES.getlist("additional_images")
        for image in additional_images:
            ProductImage.objects.create(
                variant=variant, image_url=image, is_primary=False
            )

        messages.success(request, "Variant added successfully.")
        return redirect("manage_variants", product_slug=product.slug)

    # GET section: check whether user requested editing
    edit_variant_id = request.GET.get("edit_variant_id")
    if edit_variant_id:
        edit_variant = get_object_or_404(
            ProductVariant, id=edit_variant_id, product=product
        )
        selected_option_ids = list(
            VariantAttributeBridge.objects.filter(variant=edit_variant).values_list(
                "option_id", flat=True
            )
        )

    return render(
        request,
        "seller_templates/manage_variants.html",
        {
            "product": product,
            "attributes": attributes,
            "variants": variants,
            "edit_variant": edit_variant,
            "selected_option_ids": selected_option_ids,
        },
    )


@verified_seller_required
def delete_product(request, product_slug):
    seller = request.user.seller_profile
    product = get_object_or_404(Product, slug=product_slug, seller=seller)

    if request.method == "POST":
        product.delete()
        return redirect("dashboard")

    return redirect("dashboard")


@verified_seller_required
def customer_reviews(request):
    seller = request.user.seller_profile

    if request.method == "POST":
        review_id = request.POST.get("review_id")
        reply_text = request.POST.get("reply_text", "").strip()

        if review_id and reply_text:
            review = get_object_or_404(Review, id=review_id, product__seller=seller)
            review.seller_reply = reply_text
            review.save()
            messages.success(request, "Reply posted successfully.")
        else:
            messages.error(request, "Please provide a reply message.")

        return redirect("customer_reviews")

    filter_opt = request.GET.get("filter", "all")
    reviews = (
        Review.objects.filter(product__seller=seller)
        .select_related("user", "product")
        .order_by("-created_at")
    )

    if filter_opt == "needs_reply":
        reviews = reviews.filter(
            Q(seller_reply__isnull=True) | Q(seller_reply__exact="")
        )
    elif filter_opt == "positive":
        reviews = reviews.filter(rating__gte=4)
    elif filter_opt == "critical":
        reviews = reviews.filter(rating__lte=3)

    from django.core.paginator import Paginator

    paginator = Paginator(reviews, settings.PAGINATE_BY)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    total_reviews = Review.objects.filter(product__seller=seller).count()
    average_rating = Review.objects.filter(product__seller=seller).aggregate(
        avg=Avg("rating")
    )
    store_rating = round(average_rating["avg"] or 0, 1)

    return render(
        request,
        "seller_templates/reviews_from_customer.html",
        {
            "reviews": page_obj,
            "total_reviews": total_reviews,
            "store_rating": store_rating,
            "filter": filter_opt,
        },
    )


@verified_seller_required
def seller_customers_orders(request):
    seller = request.user.seller_profile
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all").lower()

    orders = (
        OrderItem.objects.filter(seller=seller)
        .select_related("order__user", "variant", "variant__product")
        .prefetch_related("variant__images")
        .order_by("-order__ordered_at")
    )

    if status and status != "all":
        orders = orders.filter(order__order_status__iexact=status)

    if query:
        orders = orders.filter(
            Q(order__order_number__icontains=query)
            | Q(order__user__first_name__icontains=query)
            | Q(order__user__last_name__icontains=query)
            | Q(order__user__username__icontains=query)
            | Q(variant__product__name__icontains=query)
        )

    from django.core.paginator import Paginator

    paginator = Paginator(orders, settings.PAGINATE_BY)
    page_number = request.GET.get("page")
    orders_page = paginator.get_page(page_number)

    context = {
        "orders": orders_page,
        "page_obj": orders_page,
        "paginator": paginator,
        "request": request,
        "current_status": status,
        "query": query,
    }
    return render(request, "seller_templates/customer_orders.html", context)


@verified_seller_required
def update_order_status(request):
    if request.method == "POST":
        seller = request.user.seller_profile
        order_id = request.POST.get("order_id")
        status = request.POST.get("status")

        order = get_object_or_404(Order, id=order_id)

        seller_items = OrderItem.objects.filter(order=order, seller=seller)
        if not seller_items.exists():
            return redirect("seller_customers_orders")

        if status in ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]:
            order.order_status = status
            order.save()

    return redirect("seller_customers_orders")


def seller_analytics(request):
    return render(request, "seller_templates/selleranalytics.html")
