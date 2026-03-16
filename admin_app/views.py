from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from core.models import *
from seller.models import *
from core.decorators import admin_required
from .forms import AttributeForm, AttributeOptionForm


@admin_required
def admin_dashboard_view(request):
    product_variants = ProductVariant.objects.all()
    seller = SellerProfile.objects.filter(user__role="SELLER")
    subcategories = SubCategory.objects.all()
    attributes = Attribute.objects.all()

    context = {
        "products": product_variants,
        "sellers": seller,
        "subcategories": subcategories,
        "attributes": attributes,
    }
    return render(request, "admin_templates/admindashboard.html", context)


@admin_required
def seller_verification(request, id):
    seller = SellerProfile.objects.get_object_or_404(id=id)
    if request.method == "POST":
        status = request.POST.get("status")
        remarks = request.POST.get("remarks")
        seller.verification_status = status
        seller.admin_remarks = remarks

        # Update CustomUser field explicitly
        if status == "approved":
            seller.user.is_verified_seller = True
        else:
            seller.user.is_verified_seller = False
        seller.user.save()
        seller.save()
        messages.success(
            request, f"Seller '{seller.store_name}' {status.upper()} successfully!"
        )
        return redirect("admin_dashboard")
    context = {"seller": seller}
    return render(request, "admin_templates/seller_verification.html", context)


@admin_required
def product_verification(request, id):
    product_variant = get_object_or_404(ProductVariant, id=id)
    product = product_variant.product
    if request.method == "POST":
        status = request.POST.get("status")
        remarks = request.POST.get("remarks")
        product.approval_status = status
        product.admin_remarks = remarks
        product.save()
        return redirect(f"{reverse('admin_dashboard')}#products")
    context = {"product": product}
    return render(request, "admin_templates/product_verification.html", context)


# ==================== ATTRIBUTE MANAGEMENT FORMS ====================


@admin_required
@require_http_methods(["POST"])
def create_attribute(request):
    """Handle attribute creation via AJAX or form submission"""
    form = AttributeForm(request.POST)
    if form.is_valid():
        attribute = form.save()
        messages.success(request, f"Attribute '{attribute.name}' created successfully!")
        return JsonResponse(
            {
                "status": "success",
                "message": f"Attribute '{attribute.name}' created successfully!",
                "attribute_id": attribute.id,
                "attribute_name": attribute.name,
            }
        )
    else:
        return JsonResponse(
            {"status": "error", "message": "Invalid form data", "errors": form.errors},
            status=400,
        )


@admin_required
@require_http_methods(["POST"])
def create_attribute_option(request):
    """Handle attribute option creation via AJAX or form submission"""
    form = AttributeOptionForm(request.POST)
    if form.is_valid():
        option = form.save()
        messages.success(request, f"Option '{option.value}' added successfully!")
        return JsonResponse(
            {
                "status": "success",
                "message": f"Option '{option.value}' added to {option.attribute.name}!",
                "option_id": option.id,
                "option_value": option.value,
                "attribute": option.attribute.name,
            }
        )
    else:
        return JsonResponse(
            {"status": "error", "message": "Invalid form data", "errors": form.errors},
            status=400,
        )


@admin_required
@require_http_methods(["POST"])
def verify_seller_ajax(request):
    """Handle seller verification via AJAX"""
    seller_id = request.POST.get("seller_id")
    status = request.POST.get("status")
    remarks = request.POST.get("remarks", "")

    try:
        seller = SellerProfile.objects.get(id=seller_id)
        seller.verification_status = status
        seller.admin_remarks = remarks

        # Update CustomUser field explicitly
        if status == "approved":
            seller.user.is_verified_seller = True
        else:
            seller.user.is_verified_seller = False
        seller.user.save()

        seller.save()

        return JsonResponse(
            {
                "status": "success",
                "message": f"Seller '{seller.store_name}' status updated to {status}!",
                "seller_id": seller.id,
                "verification_status": seller.verification_status,
                "is_verified_seller": seller.user.is_verified_seller,
            }
        )
    except SellerProfile.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Seller not found"}, status=404
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@admin_required
@require_http_methods(["POST"])
def verify_product_ajax(request):
    """Handle product verification via AJAX"""
    product_variant_id = request.POST.get("product_id")
    status = request.POST.get("status")
    remarks = request.POST.get("remarks", "")

    try:
        product_variant = ProductVariant.objects.get(id=product_variant_id)
        product = product_variant.product
        product.approval_status = status
        product.admin_remarks = remarks
        product.save()

        return JsonResponse(
            {
                "status": "success",
                "message": f"Product '{product.name}' status updated to {status}!",
                "product_id": product_variant.id,
                "approval_status": product.approval_status,
            }
        )
    except ProductVariant.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Product not found"}, status=404
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
