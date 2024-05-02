from accounts import views
from accounts.views import LiveSearchView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

handler404 = views.custom_404
handler403 = views.csrf_forbidden_view

urlpatterns = [
    # Static Pages Url's
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.landing_page, name="landing"),
    path("newsletter", views.newsletter, name="newsletter"),
    path("landing_blog/", views.landing_blog, name="landing_blog"),
    path("term-and-condition/", views.term_and_condition, name="term-and-condition"),
    path("privacy-notes/", views.privacy_notes, name="privacy-notes"),
    path("contact/", views.contact_page, name="contact_page"),
    # Authentication Urls
    path("check-email/", views.check_email, name="check_email"),
    path("login_page", views.login_page, name="login_page"),
    path("signup_page", views.signup_page, name="signup_page"),
    path("signup_user", views.signup_user, name="signup_user"),
    path("forget_password", views.forget_password, name="forget_password"),
    path("change_password", views.change_password, name="change_password"),
    path(
        "change_password_page/<token>/",
        views.change_password_page,
        name="change_password_page",
    ),
    path("logout_user/", views.logout_user, name="logout_user"),
    path("check_user/", views.check_user, name="check_user"),
    # User Profile Url's
    path("edit_profile", views.edit_profile, name="edit_profile"),
    path("upadate_profile", views.upadate_profile, name="upadate_profile"),
    path("delete_account/", views.delete_account, name="delete_account"),
    # Dashboard, Events and Venues
    # path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "event-details/<event_id>/<venue_id>", views.event_details, name="ticket_info"
    ),
    path("search_event", views.search_event, name="search_event"),
    path("events/", views.events, name="events"),
    path("events/search/", views.event_search, name="event_search"),
    path("live-search/", LiveSearchView.as_view(), name="live_search"),
    path(
        "autocomplete/",
        views.EventAutocomplete.as_view(),
        name="event-autocomplete",
    ),
    path(
        "get_venues_for_event/<str:event_name>/",
        views.get_venues_for_event,
        name="get_venues_for_event",
    ),
    path(
        "get_dates_and_times_for_event_and_venue/<str:event_name>/<str:venue_name>/",
        views.get_dates_and_times_for_event_and_venue,
        name="get_dates_and_times_for_event_and_venue",
    ),
    # Payment Url's
    path("price/", views.price, name="price"),
    path("config/", views.stripe_config),
    path("create-checkout-session/", views.create_checkout_session),
    path("success/", views.success_payment, name="success_payment"),
    path("cancelled/", views.cancel_payment, name="cancel_payment"),
    # Preferences Url's
    path("preferences/", views.preferences, name="preferences"),
    path("update_preference/", views.update_preference, name="update_preference"),
    # Post ticket, Swap Ticket and Exchnage Url's
    path("available_tickets/", views.available_tickets, name="available_tickets"),
    path("swap_tickets_by_day/", views.swap_tickets_by_day, name="swap_tickets_by_day"),
    path(
        "load_all_swap_tickets/",
        views.load_all_swap_tickets,
        name="load_all_swap_tickets",
    ),
    path("exchange_tickets/", views.exchange_tickets, name="exchange_tickets"),
    path(
        "exchange_tickets/<str:name>?",
        views.exchange_tickets_name,
        name="exchange_tickets_name",
    ),
    path("post_ticket/", views.post_ticket, name="post_ticket"),
    path(
        "exchange_tickets/search_tickets/<str:event_name>",
        views.search_tickets,
        name="search_tickets",
    ),  # used for ajax call
    path(
        "request_exchange_tickets/<str:id>/search_tickets/<str:event_name>",
        views.search_tickets,
        name="search_tickets",
    ),  # used for ajax call
    path(
        "filter_event/search_tickets/<str:event_name>",
        views.search_tickets,
        name="search_tickets",
    ),  # used for ajax call
    path(
        "exchange_specific_ticket/<str:id>/search_tickets/<str:event_name>",
        views.search_tickets,
        name="search_tickets",
    ),  # used for ajax call
    path(
        "exchange_tickets/user_tickets/", views.user_tickets, name="user_tickets"
    ),  # used for ajax call
    path(
        "exchange_specific_ticket/<str:id>/user_tickets/",
        views.user_tickets,
        name="user_tickets",
    ),  # used for ajax call
    path(
        "exchange_specific_ticket/<str:id>/",
        views.exchange_specific_ticket,
        name="exchange_specific_ticket",
    ),
    path(
        "request_exchange_tickets/<str:id>/",
        views.request_exchange_tickets,
        name="request_exchange_tickets",
    ),
    path(
        "request_exchange_tickets/<str:id>/user_tickets/",
        views.user_available_tickets,
        name="user_tickets",
    ),
    path(
        "request_exchange_tickets/<str:id>/<str:ticket_id>/",
        views.specific_user_tickets,
        name="user_tickets",
    ),
    path(
        "exchange_tickets_name/user_tickets/",
        views.user_available_tickets,
        name="user_tickets",
    ),
    path(
        "request_exchange_tickets/<str:id>/<str:ticket_id>/user_tickets/",
        views.user_available_tickets,
        name="user_tickets",
    ),
    path("swap_ticket/", views.swap_ticket, name="swap_ticket"),
    path("my_tickets", views.mytickets, name="my_tickets"),
    path("pending_ticket", views.pending_ticket, name="pending_ticket"),
    path(
        "approve_exchange/<int:id>/",
        views.approve_exchange,
        name="approve_exchange",
    ),
    path(
        "decline_exchange/<int:ticket_id>/",
        views.decline_exchange,
        name="decline_exchange",
    ),
    path("history", views.history, name="history"),
    path(
        "filter_event/<int:event_id>",
        views.filter_event,
        name="filter_event",
    ),
    path(
        "filter_event/user_tickets/",
        views.user_tickets,
        name="user_tickets",  # Changed the name to distinguish it from the previous pattern
    ),
    path("info_page/<int:id>/", views.info_page, name="info_page"),
    # Blogs Url's
    # path("blogs/", views.all_blogs, name="all_blogs"),
    path(
        "blogs/category/<int:category_id>/",
        views.blogs_by_category,
        name="blogs_by_category",
    ),
    path("blogs/<int:blog_id>/", views.blog_detail, name="blog_detail"),
    # State and City Url's
    path("get_cities/<state_id>/", views.get_cities, name="get_cities"),
    path(
        "discard-exchange/<int:ticket_id>/",
        views.discard_exchange,
        name="discard_exchange",
    ),
    path("delete_ticket/<str:id>/", views.delete_ticket, name="delete_ticket"),
    path("cancel-subscription/", views.cancel_subscription, name="cancel_subscription"),
    path("add-message/", views.add_message, name="add_message"),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
