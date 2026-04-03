from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from core.decorators import seller_required, verified_seller_required
from .models import *
from core.models import *
from core.models import Category
from django.db.models import Count, Avg, Max, Sum, Q, F
from customer.models import Order, OrderItem, Review
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
import random
import json
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

    approved_products = products.filter(approval_status="approved").count()
    pending_products = products.filter(approval_status="pending").count()
    rejected_products = products.filter(approval_status="rejected").count()

    context = {
        "products": products,
        "total_products": total_products,
        "approved_products": approved_products,
        "pending_products": pending_products,
        "rejected_products": rejected_products,
        "active_orders": active_orders,
        "needs_shipping": needs_shipping,
        "average_rating": avg_rating,
        "total_reviews": total_reviews,
        "total_orders": total_orders,
        "pending_actions": pending_actions,
        "total_revenue": revenue_from_completed,
    }

    return render(request, "seller_templates/sellerdashboard.html", context)


@verified_seller_required
def add_product(request):
    seller = request.user.seller_profile
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()

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
        
    }
    return render(request, "seller_templates/add_product.html", context)
@verified_seller_required
def update_product(request, product_slug):
    seller = request.user.seller_profile
    product = get_object_or_404(Product, slug=product_slug, seller=seller)
    variant = product.variants.first()
    primary_image = variant.images.filter(is_primary=True).first()
    additional_images = variant.images.filter(is_primary=False)

    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()

    if request.method == "POST":

        
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.brand = request.POST.get("brand")
        product.model_number = request.POST.get("model_number")
        product.subcategory_id = request.POST.get("subcategory")
        product.save()

        
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

        
        uploaded_primary_image = request.FILES.get("primary_image")
        if uploaded_primary_image:
            ProductImage.objects.filter(variant=variant, is_primary=True).delete()
            ProductImage.objects.create(
                variant=variant,
                image_url=uploaded_primary_image,
                is_primary=True
            )

        uploaded_additional_images = request.FILES.getlist("additional_images")
        for image in uploaded_additional_images:
            ProductImage.objects.create(
                variant=variant,
                image_url=image,
                is_primary=False
            )

        return redirect("dashboard")

    
    context = {
        "product": product,
        "variant": variant,
        "categories": categories,
        "subcategories": subcategories,
        "primary_image": primary_image,
        "additional_images": additional_images,
    }

    return render(request, "seller_templates/update_product.html", context)

@verified_seller_required
def delete_product(request, product_slug):
    seller = request.user.seller_profile
    product = get_object_or_404(Product, slug=product_slug, seller=seller)

    if request.method == "POST":
        product.delete()
        return redirect("dashboard")

    return redirect("dashboard")


@login_required
@seller_required
def seller_settings_view(request):
    user = request.user
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
        elif len(new_password) < 8:
            messages.error(request, "New password must be at least 8 characters long.")
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password changed successfully.")
            return redirect("profile")

    return render(request, "seller_templates/settings.html", {"user": user})


@verified_seller_required
def seller_inventory_view(request):
    seller = request.user.seller_profile
    variants = ProductVariant.objects.filter(product__seller=seller).select_related("product").order_by("-id")
    logs = (
        InventoryLog.objects.filter(variant__product__seller=seller)
        .select_related("variant", "performed_by")
        .order_by("-created_at")[:200]
    )

    for log in logs:
        log.old_stock = log.variant.stock_quantity - log.change_amount

    if request.method == "POST":
        variant_id = request.POST.get("variant_id")
        quantity = request.POST.get("quantity")
        reason = request.POST.get("reason", "Inventory update")

        if not variant_id or not quantity:
            messages.error(request, "Please select a variant and quantity to update.")
            return redirect("seller_inventory")

        variant = get_object_or_404(ProductVariant, id=variant_id, product__seller=seller)

        try:
            quantity_delta = int(quantity)
        except ValueError:
            messages.error(request, "Quantity must be an integer.")
            return redirect("seller_inventory")

        old_stock = variant.stock_quantity
        new_stock = old_stock + quantity_delta
        if new_stock < 0:
            messages.error(request, "Stock cannot go below zero.")
            return redirect("seller_inventory")

        variant.stock_quantity = new_stock
        variant.save()

        InventoryLog.objects.create(
            variant=variant,
            change_amount=quantity_delta,
            reason=reason,
            performed_by=request.user,
        )

        messages.success(request, f"Inventory updated for {variant.sku_code}: {old_stock} → {new_stock}.")
        return redirect("seller_inventory")

    return render(
        request,
        "seller_templates/seller_inventory.html",
        {
            "variants": variants,
            "logs": logs,
        },
    )


#####################################################################################################################
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

import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction

def seller_bridge(request):
    role = request.GET.get("role")
    if (
        request.user.is_authenticated
        and SellerProfile.objects.filter(user=request.user).exists()
        and getattr(request.user, 'is_verified_seller', False) 
    ):
        return redirect("dashboard")

    if request.method == "POST":

        if request.user.is_authenticated:
            seller_profile, created = SellerProfile.objects.get_or_create(
                user=request.user
            )
            seller_profile.store_name = request.POST.get("store_name")
            seller_profile.gst_number = request.POST.get("gst_no", "")
            seller_profile.pan_number = request.POST.get("pan_no", "")
            seller_profile.bank_account_number = request.POST.get("bank_account_number", "")
            seller_profile.ifsc_code = request.POST.get("ifsc_code", "")
            seller_profile.description = request.POST.get("description", "")
            seller_profile.business_address = request.POST.get("business_address", "")

            if request.FILES.get("logo"):
                seller_profile.store_image = request.FILES.get("logo")

            seller_profile.save()

            user = request.user
            user.is_seller = True
            phone = request.POST.get("phone_number")
            if phone:
                user.phone_number = phone
                
            user.save()
            user.refresh_from_db()

            messages.success(request, "Seller application submitted successfully!")
            return redirect("seller-profile") 

        else:
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            username = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip()
            phone_number = request.POST.get("phone_number", "").strip()
            password = request.POST.get("password")
            cnf_password = request.POST.get("confirm_password")

            if password != cnf_password:
                messages.error(request, "Passwords do not match!")
                return render(request, "seller_templates/seller_bridge.html", {
                    "email": email, "username": username
                })

            if not username:
                base_username = f"{first_name.lower()}{last_name.lower()}"
                if not base_username:
                    base_username = email.split('@')[0]
                username = base_username
                if CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}{random.randint(1000, 9999)}"

            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, "Username already exists! Please choose another.")
                return render(request, "seller_templates/seller_bridge.html", {"email": email})

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email already exists! Please log in instead.")
                return render(request, "seller_templates/seller_bridge.html", {"username": username})
            try:
                with transaction.atomic():
                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=phone_number,
                        role="SELLER",
                        is_seller=True,
                    )
                    SellerProfile.objects.create(
                        user=user,
                        store_name=request.POST.get("store_name"),
                        business_address=request.POST.get("business_address", ""),
                        gst_number=request.POST.get("gst_no", ""),
                        pan_number=request.POST.get("pan_no", ""),
                        description=request.POST.get("description", ""),
                        bank_account_number=request.POST.get("bank_account_number", ""),
                        ifsc_code=request.POST.get("ifsc_code", ""),
                        store_image=request.FILES.get("logo"),
                    )
                    
                messages.success(request, "Account created successfully! Please log in.")
                return redirect("login")
                
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return render(request, "seller_templates/seller_bridge.html")

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
    }
    return render(request, "seller_templates/add_product.html", context)


@verified_seller_required
def update_product(request, product_slug):
    seller = request.user.seller_profile
    product = get_object_or_404(Product, slug=product_slug, seller=seller)
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    variant = product.variants.first()
    primary_image = None
    additional_images = []

    if variant:
        primary_image = ProductImage.objects.filter(variant=variant, is_primary=True).first()
        additional_images = ProductImage.objects.filter(variant=variant, is_primary=False)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.brand = request.POST.get("brand")
        product.save()
        return redirect("dashboard")

    context = {
        "product": product,
        "categories": categories,
        "subcategories": subcategories,
        "variant": variant,
        "primary_image": primary_image,
        "additional_images": additional_images,
    }
    return render(request, "seller_templates/update_product.html", context)


@verified_seller_required
def manage_variants(request, product_slug):
    seller = request.user.seller_profile
    product = get_object_or_404(Product, slug=product_slug, seller=seller)
    variants = product.variants.prefetch_related("images")

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

    edit_variant_id = request.GET.get("edit_variant_id")
    if edit_variant_id:
        edit_variant = get_object_or_404(
            ProductVariant, id=edit_variant_id, product=product
        )

    return render(
        request,
        "seller_templates/manage_variants.html",
        {
            "product": product,
            "variants": variants,
            "edit_variant": edit_variant,
        },
    )




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

@verified_seller_required
def seller_analytics(request):
    seller = request.user.seller_profile
    
    # Get last 12 months data for sales chart
    today = timezone.now()
    months_back = today - timedelta(days=365)
    
    # Sales revenue by month (last 12 months)
    monthly_sales = []
    monthly_labels = []
    for i in range(11, -1, -1):
        month_date = today - timedelta(days=30*i)
        start_date = month_date.replace(day=1)
        if i == 0:
            end_date = today
        else:
            end_date = (month_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        
        revenue = OrderItem.objects.filter(
            seller=seller,
            status='delivered',
            order__ordered_at__gte=start_date,
            order__ordered_at__lt=end_date
        ).aggregate(total=Sum('price_at_purchase'))['total'] or 0
        
        monthly_sales.append(float(revenue))
        monthly_labels.append(start_date.strftime('%b'))
    
    # Daily sales data for current week
    daily_sales = []
    daily_labels = []
    for i in range(6, -1, -1):
        day_date = today - timedelta(days=i)
        day_start = day_date.replace(hour=0, minute=0, second=0)
        day_end = day_date.replace(hour=23, minute=59, second=59)
        
        revenue = OrderItem.objects.filter(
            seller=seller,
            status='delivered',
            order__ordered_at__gte=day_start,
            order__ordered_at__lte=day_end
        ).aggregate(total=Sum('price_at_purchase'))['total'] or 0
        
        daily_sales.append(float(revenue))
        daily_labels.append(day_date.strftime('%a'))
    
    # Top selling products
    top_products = OrderItem.objects.filter(
        seller=seller
    ).values(
        'variant__product__name'
    ).annotate(
        total_sold=Count('id')
    ).order_by('-total_sold')[:5]
    
    top_products_data = []
    top_products_labels = []
    for item in top_products:
        top_products_labels.append(item['variant__product__name'][:15])
        top_products_data.append(item['total_sold'])
    
    # Category distribution
    products = Product.objects.filter(seller=seller)
    category_dist = products.values(
        'subcategory__name'
    ).annotate(count=Count('id')).order_by('-count')
    
    category_labels = []
    category_data = []
    for cat in category_dist:
        if cat['subcategory__name']:
            category_labels.append(cat['subcategory__name'][:15])
            category_data.append(cat['count'])
    
    # Order status breakdown
    order_statuses = OrderItem.objects.filter(
        seller=seller
    ).values('status').annotate(count=Count('id')).order_by('-count')
    
    order_status_labels = []
    order_status_data = []
    order_status_colors = {
        'pending': '#F59E0B',
        'processing': '#3B82F6', 
        'shipped': '#8B5CF6',
        'delivered': '#10B981',
        'cancelled': '#EF4444',
        'return_requested': '#EC4899',
        'returned': '#6B7280'
    }
    
    for status in order_statuses:
        order_status_labels.append(status['status'].replace('_', ' ').title())
        order_status_data.append(status['count'])
    
    # Get inventory logs
    logs = InventoryLog.objects.filter(
        variant__product__seller=seller
    ).select_related(
        'variant', 'variant__product', 'performed_by'
    )[:15]
    
    # Summary metrics
    total_revenue = OrderItem.objects.filter(
        seller=seller,
        status='delivered'
    ).aggregate(total=Sum('price_at_purchase'))['total'] or 0
    
    total_orders = OrderItem.objects.filter(
        seller=seller
    ).values('order_id').distinct().count()
    
    total_items_sold = OrderItem.objects.filter(
        seller=seller,
        status='delivered'
    ).count()
    
    avg_rating = Review.objects.filter(
        product__seller=seller
    ).aggregate(avg=Avg('rating'))['avg'] or 0
    
    avg_rating = round(avg_rating, 2)
    
    # Monthly order count for trend
    monthly_orders = []
    for i in range(11, -1, -1):
        month_date = today - timedelta(days=30*i)
        start_date = month_date.replace(day=1)
        if i == 0:
            end_date = today
        else:
            end_date = (month_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        
        count = OrderItem.objects.filter(
            seller=seller,
            order__ordered_at__gte=start_date,
            order__ordered_at__lt=end_date
        ).values('order_id').distinct().count()
        
        monthly_orders.append(count)

    context = {
        'logs': logs,
        'monthly_sales': json.dumps(monthly_sales),
        'monthly_labels': json.dumps(monthly_labels),
        'daily_sales': json.dumps(daily_sales),
        'daily_labels': json.dumps(daily_labels),
        'top_products_data': json.dumps(top_products_data),
        'top_products_labels': json.dumps(top_products_labels),
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'order_status_labels': json.dumps(order_status_labels),
        'order_status_data': json.dumps(order_status_data),
        'order_status_colors': json.dumps([order_status_colors.get(status['status'], '#6B7280') for status in order_statuses]),
        'total_revenue': round(total_revenue, 2),
        'total_orders': total_orders,
        'total_items_sold': total_items_sold,
        'avg_rating': avg_rating,
        'monthly_orders': json.dumps(monthly_orders),
    }
    
    return render(request, 'seller_templates/selleranalytics.html', context)
@verified_seller_required
def delete_product_image(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id)
    if image.variant.product.seller != request.user.seller_profile:
        return redirect("dashboard")

    if request.method == "POST":
        image.delete()

    return redirect(request.META.get("HTTP_REFERER"))
