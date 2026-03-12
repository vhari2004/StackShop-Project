from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
from core.models import Category
from django.db.models import Count, Sum, Max
from customer.models import Order, OrderItem


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
    return render(
        request, "seller_templates/sellerdashboard.html", {"products": products}
    )


def seller_bridge(request):
    if (
        request.user.is_authenticated
        and SellerProfile.objects.filter(user=request.user).exists()
    ):
        return redirect("seller-profile")

    if request.user.is_authenticated and request.method == "POST":
        seller_profile, created = SellerProfile.objects.get_or_create(user=request.user)

        seller_profile.store_name = request.POST.get("store_name")
        seller_profile.gst_number = request.POST.get("tax_id", "")
        seller_profile.pan_number = request.POST.get("pan_number", "")
        seller_profile.bank_account_number = request.POST.get("bank_account_number", "")
        seller_profile.ifsc_code = request.POST.get("ifsc_code", "")
        seller_profile.business_address = request.POST.get("description", "")

        if request.FILES.get("logo"):
            seller_profile.store_image = request.FILES.get("logo")

        seller_profile.save()

        user = request.user
        user.is_seller = True
        user.role = "SELLER"
        user.save()  
        user.refresh_from_db()  

        return redirect("seller-profile")
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
def update_product(request, product_id):
    seller = request.user.seller_profile
    product = get_object_or_404(Product, id=product_id, seller=seller)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.brand = request.POST.get("brand")
        product.save()
        return redirect("dashboard")

    return render(request, "seller_templates/update_product.html", {"product": product})


@verified_seller_required
def delete_product(request, product_id):
    seller = request.user.seller_profile
    product = get_object_or_404(Product, id=product_id, seller=seller)

    if request.method == "POST":
        product.delete()
        return redirect("dashboard")

    return redirect("dashboard")

@verified_seller_required
def customer_reviews(request):
    return render(request, "seller_templates/reviews_from_customer.html")

@verified_seller_required
def seller_customers_orders(request):
    seller = request.user.seller_profile
    orders = (
        OrderItem.objects.filter(seller=seller)
        .select_related("order__user", "variant", "variant__product")
        .prefetch_related("variant__images")
    )

    context = {"orders": orders}
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

