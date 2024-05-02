from audioop import reverse
from accounts.models import (
    ApprovedExchange,
    BlogPost,
    Category,
    City,
    ContactUs,
    DeletedTickets,
    ExchangeTicket,
    History,
    LogEntry,
    NewsLetter,
    PostTickets,
    Profile,
    PromoCode,
    State,
    TicketPreference,
    UserPreferences,
)

# user later
# from django.db.models.signals import post_save, post_delete, pre_save
# from django.dispatch import receiver
# from django.contrib.auth.models import User
# from django.utils.html import format_html
# from .models import StaffActivity
# from accounts.middleware import get_current_user

from django.contrib import admin

admin.site.site_header = "Ticket Barter Administration"

# Register your models here.
# admin.site.register(UserPreferences)

# admin.site.register(StaffActivity)
admin.site.register(History)
admin.site.register(Category)
admin.site.register(BlogPost)
admin.site.register(TicketPreference)
admin.site.register(State)
admin.site.register(LogEntry)
admin.site.register(City)
admin.site.register(ContactUs)
admin.site.register(PromoCode)


class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ("user", "sports", "music", "art", "family")


admin.site.register(UserPreferences, UserPreferencesAdmin)


class DeletedTicketsAdmin(admin.ModelAdmin):
    list_display = ("event_name", "venue_name", "event_date")
    search_fields = ("event_name", "venue_name", "details")


admin.site.register(DeletedTickets, DeletedTicketsAdmin)


class NewsLetterAdmin(admin.ModelAdmin):
    list_display = ("name", "email")
    search_fields = ("name", "email")


admin.site.register(NewsLetter, NewsLetterAdmin)


class ExchangeTicketAdmin(admin.ModelAdmin):
    list_display = (
        "porpose_to",
        "ticket_to_exchange",
        "porpose_from",
        "ticket_from_exchange",
    )
    search_fields = ("ticket_to_exchange", "ticket_from_exchange")


admin.site.register(ExchangeTicket, ExchangeTicketAdmin)


class ApprovedExchangeAdmin(admin.ModelAdmin):
    list_display = (
        "transfer_user_1",
        "transfer_user_1_ticket",
        "transfer_user_2",
        "transfer_user_2_ticket",
    )


admin.site.register(ApprovedExchange, ApprovedExchangeAdmin)


class PostTicketsAdmin(admin.ModelAdmin):
    list_display = ("event_name", "venue_name", "event_date", "get_review_status")
    list_filter = ("approve", "event_date")
    search_fields = ("event_name", "venue_name", "details")

    def get_review_status(self, obj):
        if obj.approve:
            return "Approved ✔️"
        else:
            return "In Review ⚠️"

    get_review_status.short_description = "Review Status"
    get_review_status.admin_order_field = (
        "review_status"  # Allows sorting by review status
    )


admin.site.register(PostTickets, PostTicketsAdmin)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "payment_status", "complete_profile")
    list_filter = ("is_payment", "complete_profile")

    actions = ["mark_as_payment_true", "mark_as_payment_false"]

    def mark_as_payment_true(self, request, queryset):
        queryset.update(is_payment=True)

    mark_as_payment_true.short_description = "Mark selected profiles as Payment True"

    def mark_as_payment_false(self, request, queryset):
        queryset.update(is_payment=False)

    mark_as_payment_false.short_description = "Mark selected profiles as Payment False"

    def payment_status(self, obj):
        if obj.is_payment:
            return "Premium ✔️"
        else:
            return "Free ⚠️"

    payment_status.short_description = "Payment Status"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Exclude required fields when updating existing instances
        if obj:
            form.base_fields["middle_name"].required = False
            form.base_fields["street_address"].required = False
            form.base_fields["apartment_number"].required = False
            form.base_fields["city"].required = False
            form.base_fields["state"].required = False
            form.base_fields["mobile"].required = False
            form.base_fields["zip_code"].required = False
            form.base_fields["promo_code"].required = False
            form.base_fields["forget_password_tocken"].required = False
            form.base_fields["tm_email"].required = False
            form.base_fields["payment_expiration_date"].required = False

        return form


admin.site.register(Profile, ProfileAdmin)

# user later
# class StaffActivityAdmin(admin.ModelAdmin):
#     list_display = (
#         "user",
#         "action",
#         "model_name",
#         "ticket_name",
#         "read",
#         "object_id_link",
#         "timestamp",
#     )
#     list_filter = ("action", "model_name")

#     def view_on_site(self, obj):
#         obj.read = True
#         obj.save()
#         return

#     def object_id_link(self, obj):
#         model_admin = self.admin_site._registry.get(obj.model_name)
#         print("model_admin ", model_admin)
#         if model_admin:
#             object_url = model_admin.url_for_object(obj.object_id)
#             print("object_url ", object_url)
#             return format_html('<a href="{}">{}</a>', object_url, obj.object_id)
#         return obj.object_id

#     object_id_link.short_description = "Object"


# admin.site.register(StaffActivity, StaffActivityAdmin)


# @receiver(post_save, sender=PostTickets)
# def create_staff_activity_on_save(sender, instance, created, **kwargs):
#     if created:
#         StaffActivity.objects.create(
#             user=instance.user,
#             ticket_name=instance.event_name,
#             action="CREATE",
#             model_name=sender.__name__,
#             object_id=instance.pk,
#         )
#     else:
#         if instance.approve and not instance.is_update:
#             user = get_current_user()
#             StaffActivity.objects.create(
#                 user=user,
#                 action="UPDATE",
#                 ticket_name=instance.event_name,
#                 model_name=sender.__name__,
#                 object_id=instance.pk,
#             )
#             instance.is_update = True
#             instance.save()


# @receiver(post_delete, sender=PostTickets)
# def create_staff_activity_on_delete(sender, instance, **kwargs):
#     StaffActivity.objects.create(
#         user=instance.user,
#         action="DELETE",
#         ticket_name=instance.event_name,
#         model_name=sender.__name__,
#         object_id=instance.pk,
#     )


# @receiver(post_save, sender=ApprovedExchange)
# def create_staff_activity_on_Approved_exchanges(sender, instance, created, **kwargs):
#     if created:
#         StaffActivity.objects.create(
#             user=instance.transfer_user_1,
#             action="CREATE",
#             ticket_name=instance.transfer_user_1_ticket.event_name,
#             model_name=sender.__name__,
#             object_id=instance.pk,
#         )
#     else:
#         user = get_current_user()
#         StaffActivity.objects.create(
#             user=user,
#             action="UPDATE",
#             model_name=sender.__name__,
#             object_id=instance.pk,
#         )
