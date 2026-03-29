from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    Cart,
    CartItem,
    Wishlist,
    WishlistItem,
    Review,
    Order,
    OrderItem,
    PaymentOrder,
    ReactivationRequest,
)

admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Wishlist)
admin.site.register(WishlistItem)
admin.site.register(Review)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(PaymentOrder)


def _get_email_sender():
    return getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER or "noreply@stackshop.com")


def _send_email(recipient_email, subject, message):
    if not recipient_email:
        return
    send_mail(subject, message, _get_email_sender(), [recipient_email], fail_silently=True)


class ReactivationRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "requested_at")
    list_filter = ("status", "requested_at")
    search_fields = ("user__username", "user__email")
    actions = ["approve_reactivation", "reject_reactivation"]

    def approve_reactivation(self, request, queryset):
        for obj in queryset.filter(status="PENDING"):
            obj.user.is_active = True
            obj.user.save()
            obj.status = "APPROVED"
            obj.admin_notes = "Approved by admin."
            obj.save()

            subject = "StackShop Account Reactivated"
            message = (
                f"Hello {obj.user.get_full_name() or obj.user.username},\n\n"
                "Your StackShop account has been reactivated by an administrator. "
                "You can now sign in again.\n\n"
                "Thank you,\nStackShop Team"
            )
            _send_email(obj.user.email, subject, message)

        self.message_user(request, "Selected reactivation requests have been approved.")
    approve_reactivation.short_description = "Approve selected reactivation requests"

    def reject_reactivation(self, request, queryset):
        for obj in queryset.filter(status="PENDING"):
            obj.status = "REJECTED"
            obj.admin_notes = "Rejected by admin."
            obj.save()

            subject = "StackShop Reactivation Request Rejected"
            message = (
                f"Hello {obj.user.get_full_name() or obj.user.username},\n\n"
                "Your StackShop account reactivation request has been rejected by an administrator. "
                "If you believe this is a mistake, please contact support.\n\n"
                "Thank you,\nStackShop Team"
            )
            _send_email(obj.user.email, subject, message)

        self.message_user(request, "Selected reactivation requests have been rejected.")
    reject_reactivation.short_description = "Reject selected reactivation requests"


admin.site.register(ReactivationRequest, ReactivationRequestAdmin)