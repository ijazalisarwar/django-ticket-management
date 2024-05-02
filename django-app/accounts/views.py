import ast
import datetime
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pytz import UTC
import requests
import stripe
from operator import itemgetter
from accounts.helpers import (
    exchange_request_approve_mail,
    exchange_request_decline_mail,
    exchange_request_mail,
    forget_password_mail,
    payment_reciept_mail,
)
from accounts.city_state import save_states_and_cities, import_cities_data
from accounts.models import (
    ApprovedExchange,
    BlogPost,
    Category,
    City,
    ContactUs,
    ExchangeTicket,
    History,
    LogEntry,
    NewsLetter,
    PostTickets,
    Profile,
    State,
    TicketPreference,
    UserPreferences,
)
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F, Q
from django.http import JsonResponse
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views import View
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET
from ticket_master.models import Classification, Event, Venue


def custom_404(request, *args, **kwargs):
    return render(request, "404.html", status=404)


def csrf_forbidden_view(request, exception=None):
    return render(request, "csrf_forbidden.html", status=403)


def landing_page(request):
    return render(request, "landingpage/landing_page.html")


def term_and_condition(request):
    return render(request, "terms_and_condition.html")


def privacy_notes(request):
    return render(request, "privacy_notes.html")


def log_exception(view_name, error_message):
    timestamp = timezone.now()
    LogEntry.objects.create(
        view_name=view_name, error_message=error_message, timestamp=timestamp
    )


def landing_blog(request):
    try:
        categories = Category.objects.all()
        query = request.GET.get("q")
        if query:
            blogs = BlogPost.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query),
                category__name="Blog",
            )
            podcasts = BlogPost.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query),
                category__name="Podcasts",
            )
        else:
            # If no search query, get all blogs and podcasts
            blogs = BlogPost.objects.filter(category__name="Blog")
            podcasts = BlogPost.objects.filter(category__name="Podcasts")
        return render(
            request,
            "landingpage/blog.html",
            {"blogs": blogs, "podcasts": podcasts, "categories": categories},
        )
    except Exception as e:
        log_exception("Blog View", str(e))


def newsletter(request):
    try:
        if request.method == "POST":
            name = request.POST["name"]
            email = request.POST["email"]
            news_letter = NewsLetter(name=name, email=email)
            news_letter.save()
            messages.success(
                request, "Thank you for signing up Ticket Barter Newsletter!"
            )
            return redirect("landing")
        return render(request, "landingpage/landing_page.html")
    except Exception as e:
        log_exception("NewsLetter View", str(e))


def contact_page(request):
    try:
        if request.method == "POST":
            name = request.POST["name"]
            email = request.POST["email"]
            description = request.POST["description"]
            contact_us = ContactUs(name=name, email=email, description=description)
            contact_us.save()
            messages.success(request, "Your query submitted successfully!")
            return redirect("contact_page")
        return render(request, "landingpage/contact.html")
    except Exception as e:
        log_exception("Contact Page View", str(e))


@login_required(login_url="login_page")
def info_page(request, id):
    post_ticket = PostTickets.objects.get(id=id)
    return render(request, "info_page.html", {"post_ticket": post_ticket})


# Blog Views
# def all_blogs(request):
#     query = request.GET.get("q")
#     blogs = BlogPost.objects.filter(Q(title__icontains=query) | Q(description__icontains=query)) if query else BlogPost.objects.all()
#     return render(request, "blog.html", {"blogs": blogs, "categories":Category.objects.all()})


def blogs_by_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id)
        query = request.GET.get("q")
        blogs = (
            BlogPost.objects.filter(
                Q(category=category)
                & (Q(title__icontains=query) | Q(description__icontains=query))
            )
            if query
            else BlogPost.objects.filter(category=category)
        )
        return render(
            request,
            "blogs_by_category.html",
            {
                "blogs": blogs,
                "categories": Category.objects.all(),
                "selected_category": category,
            },
        )
    except Exception as e:
        log_exception("Blog by Category View", str(e))


def blog_detail(request, blog_id):
    try:
        blog = get_object_or_404(BlogPost, id=blog_id)
        return render(request, "blogdetail.html", {"blog": blog})
    except Exception as e:
        log_exception("Blog Detail View", str(e))


def blog(request):
    return render(request, "blog.html")


# Authentication Views
@csrf_protect
def login_page(request):
    try:
        if request.user.is_authenticated:
            preference = UserPreferences.objects.filter(user_id=request.user.id).first()
            return redirect("preferences" if not preference else "dashboard")
        if request.method == "POST":
            email = request.POST["email"].lower()
            password = request.POST["password"]
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                request.session.set_expiry(86400)
                preference_exists = UserPreferences.objects.filter(
                    user_id=user.id
                ).exists()
                is_subscription = check_subscription(user)
                if not is_subscription:
                    return redirect("price")
                return redirect("preferences" if not preference_exists else "dashboard")
            else:
                messages.error(request, "Invalid Credentials")
                return render(request, "login.html")
        return render(request, "login.html")
    except Exception as e:
        log_exception("Login Page View", str(e))


def signup_page(request):
    try:
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(
            request,
            "signup.html",
            {
                "states": State.objects.all().order_by("name"),
                "cities": City.objects.all().order_by("name"),
            },
        )
    except Exception as e:
        log_exception("Sign Up Page View", str(e))


def signup_user(request):
    try:
        dob = request.POST["dob"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        normal_email = request.POST["email"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        city = request.POST["city"]
        state = request.POST["state"]
        zip_code = request.POST.get("zip_code", 0)
        email = normal_email.lower()
        is_payment = False  # Default value for is_payment
        expiration_date = None  # Default value for expiration_date

        # Get the current datetime
        current_datetime = datetime.now()
        if User.objects.filter(email=email).exists():
            get_user = User.objects.filter(email=email)
            check_pass = check_password(password, get_user[0].password)
            if not check_pass:
                messages.error(request, "Forget the Password For Log In")
                return redirect("signup_page")

        if User.objects.filter(email=email).exists():
            get_user = User.objects.filter(email=email)
            check_pass = check_password(password, get_user[0].password)
            if not check_pass:
                messages.error(request, "Forget the Password For Log In")
                return redirect("/")
        # Check if the password meets the minimum length requirement
        if len(password) < 8 or len(confirm_password) < 8:
            messages.error(request, "Password Length Minimum 8 Characters")
            return redirect("signup_page")

        # Check if the email already exists in the database
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email address already exists")
            return redirect("signup_page")

        # Check if the passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup_page")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        Profile.objects.create(
            user=user,
            city=city,
            state=state,
            dob=dob,
            zip_code=zip_code,
            is_payment=is_payment,
            payment_expiration_date=expiration_date,
        )

        auth_user = authenticate(request, username=email, password=password)
        if auth_user:
            login(request, auth_user)
            request.session["email"] = email
            return redirect("preferences")
        else:
            messages.error(request, "Failed to authenticate user")
            return redirect("login_page")
    except Exception as e:
        log_exception("Signup User View", str(e))


def check_user(request):
    return redirect("dashboard")


def forget_password(request):
    return render(request, "forget_password.html")


def change_password_page(request, token):
    try:
        profile = Profile.objects.get(forget_password_tocken=token)
        if request.method == "POST":
            new_password = request.POST["password1"]
            confirm_password = request.POST["password2"]
            user_id = request.POST["user_id"]
            if user_id is None:
                return redirect(
                    reverse("change_password_page", kwargs={"token": token})
                )
            if len(new_password) < 8 and len(confirm_password) < 8:
                messages.success(request, "Password length Should be Eight Digit")
                return redirect(
                    reverse("change_password_page", kwargs={"token": token})
                )
            if new_password != confirm_password:
                messages.success(request, "Password is not Match")
                return redirect(
                    reverse("change_password_page", kwargs={"token": token})
                )
            user = User.objects.get(id=user_id)
            user.username = user.email
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password has been changed")
            return redirect("login_page")
        return render(request, "change_password.html", {"user_id": profile.user.id})
    except ObjectDoesNotExist:
        messages.error(request, "Profile not found or token is invalid")
        return redirect("login_page")
    except Exception as e:
        log_exception("Change Password View", str(e))


def add_message(request):
    # Add your message here
    messages.success(
        request,
        "Your email already exists! Try with another account or with forget password.",
    )
    return JsonResponse({"status": "success"})


def change_password(request):
    try:
        if request.method == "POST":
            email = request.POST["email"]
            if not User.objects.filter(email=email).first():
                return redirect("signup_page")
            user = User.objects.get(email=email)
            try:
                profile = Profile.objects.get(user=user)
            except Profile.DoesNotExist:
                profile = Profile(user=user)

            token = str(uuid.uuid4())
            # profile = Profile.objects.get(user=user)
            profile.forget_password_tocken = token
            profile.save()
            domain = request.build_absolute_uri("/")
            forget_password_mail(domain, user.email, token)
            messages.success(
                request, "Please check your spam email OR Inbox to reset your password."
            )
            return redirect("login_page")
    except Exception as e:
        log_exception("Change Password View", str(e))


def check_email(request):
    if request.method == "POST":
        normal_email = request.POST.get("email").lower()
        email_exists = User.objects.filter(email=normal_email).exists()
        return JsonResponse({"exists": email_exists})


def logout_user(request):
    logout(request)
    return redirect("login_page")


@login_required(login_url="login_page")
def edit_profile(request):
    try:
        profile, created = Profile.objects.get_or_create(user=request.user)
        unique_residences = State.objects.all().order_by("name")
        return render(
            request,
            "update_profile.html",
            {
                "profile": profile,
                "unique_cities": City.objects.all(),
                "unique_residences": unique_residences,
            },
        )
    except Exception as e:
        log_exception("Edit Profile View", str(e))


@login_required(login_url="login_page")
def upadate_profile(request):
    try:
        if request.method == "POST":
            first_name = request.POST["first_name"]
            last_name = request.POST["last_name"]
            email = request.POST["email"]
            city = request.POST.get("city", "")
            phone = request.POST["phone"]
            state = request.POST["state"]
            raw_zip_code = request.POST.get("zip_code", "")
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.error(
                    request, "Email already exists. Please choose a different email."
                )
                return redirect("edit_profile")
            User.objects.filter(id=request.user.id).update(
                username=email, email=email, first_name=first_name, last_name=last_name
            )
            Profile.objects.filter(user_id=request.user.id).update(
                city=city, state=state, mobile=phone, zip_code=raw_zip_code
            )
            messages.success(request, "Account settings updated!")
            return redirect("dashboard")
    except Exception as e:
        log_exception("Update Profile View", str(e))


User = get_user_model()


@login_required
def delete_account(request):
    try:
        if request.method == "POST":
            confirm_delete = request.POST.get("confirm_delete", False)
            if confirm_delete:
                user = request.user
                user.delete()
                return redirect("login_page")
        return render(request, "delete_account.html")
    except Exception as e:
        log_exception("Delete Account View", str(e))


def get_cities(request, state_id):
    try:
        state = State.objects.get(name=state_id)
        cities = City.objects.filter(state=state).values("id", "name").order_by("name")
        return JsonResponse({"cities": list(cities)})
    except State.DoesNotExist:
        return JsonResponse({"error": "Invalid state name"}, status=400)


# User Preferences Views
@login_required(login_url="login_page")
def preferences(request):
    try:
        if request.method == "POST":
            sports = request.POST.getlist("sports", "[]")
            music = request.POST.getlist("music", "[]")
            art = request.POST.getlist("art", "[]")
            family = request.POST.getlist("family", "[]")
            no_of_tickets = request.POST.get("no_of_tickets", 0)
            user_pref_instance, created = UserPreferences.objects.get_or_create(
                user_id=request.user.id,
                defaults={
                    "sports": sports,
                    "music": music,
                    "art": art,
                    "family": family,
                    "no_of_tickets": no_of_tickets,
                },
            )
            profile = Profile.objects.get(user_id=request.user.id)
            profile.complete_profile = True
            profile.save()
            messages.success(request, "Preference has been saved!")
            return redirect("dashboard")
        sports = Event.objects.filter(segment_name="Sports")
        music = Event.objects.filter(segment_name="Music")
        art = Event.objects.filter(segment_name="Arts & Theatre")
        family = Event.objects.filter(segment_name="Miscellaneous")
        genre_names_sports = list(
            sports.values_list("genre_name", flat=True).distinct()
        )
        genre_names_music = list(music.values_list("genre_name", flat=True).distinct())
        genre_names_art = list(art.values_list("genre_name", flat=True).distinct())
        genre_names_family = list(
            family.values_list("genre_name", flat=True).distinct()
        )
        return render(
            request,
            "preference.html",
            {
                "genre_names_sports": genre_names_sports,
                "genre_names_music": genre_names_music,
                "genre_names_art": genre_names_art,
                "genre_names_family": genre_names_family,
            },
        )
    except Exception as e:
        log_exception("Preferences View", str(e))


@login_required(login_url="login_page")
def update_preference(request):
    try:
        preference, created = UserPreferences.objects.get_or_create(
            user_id=request.user.id,
            defaults={
                "sports": "default_league_value",
                "music": "default_favorite_team_value",
                "art": "default_favorite_venue_value",
                "family": "default_residence_value",
                "no_of_tickets": 0,
            },
        )
        if request.method == "POST":
            fields = ["sports", "music", "art", "family"]
            data = {field: request.POST.getlist(field) for field in fields}
            data["no_of_tickets"] = request.POST.get("no_of_tickets", 0)
            user_pref_instance, created = UserPreferences.objects.update_or_create(
                user_id=request.user.id, defaults=data
            )
            if not created:
                user_pref_instance.save()
            profile = Profile.objects.get(user_id=request.user.id)
            profile.complete_profile = True
            profile.save()
            messages.success(request, "Preferences have been updated")
            return redirect("dashboard")
        preference = UserPreferences.objects.get(user_id=request.user.id)
        sports = Event.objects.filter(segment_name="Sports").exclude(
            genre_name="Miscellaneous"
        )
        music = Event.objects.filter(segment_name="Music")
        art = Event.objects.filter(segment_name="Arts & Theatre").exclude(
            genre_name="Miscellaneous Theatre"
        )
        family = Event.objects.filter(segment_name="Miscellaneous")
        genre_names_sports = list(
            sports.values_list("genre_name", flat=True).distinct()
        )
        genre_names_music = list(music.values_list("genre_name", flat=True).distinct())
        genre_names_art = list(art.values_list("genre_name", flat=True).distinct())
        genre_names_family = list(
            family.values_list("genre_name", flat=True).distinct()
        )
        return render(
            request,
            "update_preferences.html",
            {
                "preference": preference,
                "genre_names_sports": genre_names_sports,
                "genre_names_music": genre_names_music,
                "genre_names_art": genre_names_art,
                "genre_names_family": genre_names_family,
            },
        )
    except Exception as e:
        log_exception("Update Preferences View", str(e))


# Dashboard Views
@login_required(login_url="login_page")
def dashboard(request):
    try:
        user = request.user
        exchange_tickets = ExchangeTicket.objects.filter(porpose_to=user)
        exchange_tickets_count = exchange_tickets.count()
        preferences = UserPreferences.objects.filter(user_id=request.user.id).first()
        if preferences:
            sports_filter = Q()
            music_filter = Q()
            art_filter = Q()
            family_filter = Q()
            try:
                sports_list = preferences.sports
                sports_list = ast.literal_eval(sports_list)
                music_list = preferences.music
                music_list = ast.literal_eval(music_list)
                art_list = preferences.art
                art_list = ast.literal_eval(art_list)
                family_list = preferences.family
                family_list = ast.literal_eval(family_list)
                for sport in sports_list:
                    sports_filter |= Q(event__genre_name__contains=sport)
                for genre in music_list:
                    music_filter |= Q(event__genre_name__contains=genre)
                for genre in art_list:
                    art_filter |= Q(event__genre_name__contains=genre)
                for genre in family_list:
                    family_filter |= Q(event__genre_name__contains=genre)
                venues = Venue.objects.filter(
                    sports_filter | music_filter | art_filter | family_filter
                )
                now_utc = datetime.now(timezone.utc)
                today = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                venues = venues.filter(event__dates__start__dateTime__gte=today)
                if venues == []:
                    now_utc = datetime.now(timezone.utc)
                    today = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                    venues = Venue.objects.filter(
                        event__dates__start__dateTime__gte=today
                    )
            except:
                now_utc = datetime.now(timezone.utc)
                today = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                venues = Venue.objects.filter(event__dates__start__dateTime__gte=today)
        else:
            now_utc = datetime.now(timezone.utc)
            today = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            venues = Venue.objects.filter(event__dates__start__dateTime__gte=today)
        venues_per_page = 12
        paginator = Paginator(venues, venues_per_page)
        page = request.GET.get("page")
        try:
            venues_page = paginator.page(page)
        except PageNotAnInteger:
            venues_page = paginator.page(1)
        except EmptyPage:
            venues_page = paginator.page(paginator.num_pages)

        return render(
            request,
            "dashboard.html",
            {"venues": venues_page, "exchange_tickets": exchange_tickets_count},
        )
    except Exception as e:
        log_exception("Dashboard View", str(e))


# Events and Venues Views
@login_required(login_url="login_page")
def events(request):
    try:
        now_utc = datetime.now(timezone.utc)
        today = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        venues = Venue.objects.filter(event__dates__start__dateTime__gte=today)
        # venues = Venue.objects.filter(event__dates__start__dateTime__gte=today).order_by("event__dates__start__dateTime")
        events_per_page = 14
        paginator = Paginator(venues, events_per_page)
        page = request.GET.get("page")
        try:
            venues_page = paginator.page(page)
        except PageNotAnInteger:
            venues_page = paginator.page(1)
        except EmptyPage:
            venues_page = paginator.page(paginator.num_pages)
        return render(request, "events.html", {"venues": venues_page})
    except Exception as e:
        log_exception("Events View", str(e))


def get_venues_for_event(request, event_name):
    event_name = event_name.replace("<", "/")
    now_utc = datetime.now(timezone.utc)
    today = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    venues = (
        Venue.objects.filter(
            event__name=event_name, event__dates__start__dateTime__gte=today
        )
        .values("name")
        .distinct()
    )
    # venues = Venue.objects.filter(event__name=event_name).values("name").distinct()
    print(venues)
    return JsonResponse({"venues": [{"name": venue["name"]} for venue in venues]})


@login_required(login_url="login_page")
def event_details(request, event_id, venue_id):
    try:
        event = Event.objects.get(event_id=event_id)
        venue = Venue.objects.filter(venue_id=venue_id).first()
        event.increment_views()
        current_datetime = timezone.now()
        thirty_minutes_ago = current_datetime - timedelta(minutes=30)
        post_tickets_count = PostTickets.objects.exclude(user_id=request.user.id)
        user_proposed_from_tickets = ExchangeTicket.objects.filter(
            porpose_from=request.user
        ).values_list("ticket_from_exchange_id", flat=True)
        post_tickets_count = (
            post_tickets_count.exclude(id__in=user_proposed_from_tickets)
            .filter(
                Q(event_date__gt=current_datetime.date())
                | Q(
                    event_date=current_datetime.date(),
                    event_time__gt=thirty_minutes_ago.time(),
                )
            )
            .filter(event_name=event.name, approve=True)
            .count()
        )
        return render(
            request,
            "ticket_information.html",
            {"event": event, "venue": venue, "post_tickets_count": post_tickets_count},
        )
    except Exception as e:
        log_exception("Event Details View", str(e))


def filter_event(request, event_id):
    try:
        post_ticket = PostTickets.objects.filter(user_id=request.user.id).last()
        swap_tickets = PostTickets.objects.filter(
            ~Q(user_id__exact=request.user.id)
            & Q(event_name__icontains=Event.objects.get(id=event_id).name)
        )
        return render(
            request,
            "exchange_tickets.html",
            {"post_ticket": post_ticket, "swap_tickets": swap_tickets},
        )
    except Exception as e:
        log_exception("Filter Event View", str(e))


@login_required(login_url="login_page")
def search_event(request):
    try:
        if request.method == "POST":
            event_name = request.POST["event_name"]
            venue_name = request.POST["venue_name"]
            search_event = Event.objects.filter(
                name__contains=event_name, venue_name__contains=venue_name
            )
            return render(request, "search_event.html", {"search_event": search_event})
        return redirect("dashboard")
    except Exception as e:
        log_exception("Search Event View", str(e))


# Whole Ticket Exchange, Swap and Post Ticket views
def search_tickets(request, id=None, event_name=None):
    try:
        current_datetime = timezone.now()
        thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
        swap_tickets = PostTickets.objects.exclude(user_id=request.user.id)
        user_proposed_from_tickets = ExchangeTicket.objects.filter(
            porpose_from=request.user
        ).values_list("ticket_from_exchange_id", flat=True)
        swap_tickets = swap_tickets.exclude(id__in=user_proposed_from_tickets).filter(
            Q(event_date__gt=current_datetime.date())
            | Q(
                event_date=current_datetime.date(),
                event_time__gt=thirty_minutes_ago.time(),
            )
        )
        swap_tickets = swap_tickets.filter(
            ~Q(user_id__exact=request.user.id) & Q(event_name__icontains=event_name)
        )
        swap_tickets = swap_tickets.filter(approve=True)
        return render(request, "search_tickets.html", {"swap_tickets": swap_tickets})
    except Exception as e:
        log_exception("Search Tickets View", str(e))


@login_required(login_url="login_page")
def post_ticket(request):
    try:
        try:
            user_profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            user_profile = Profile.objects.create(user=request.user)
            messages.error(request, "Please make a payment to post a ticket.")
            return redirect("price")
        if not user_profile.is_payment or (
            user_profile.payment_expiration_date
            and user_profile.payment_expiration_date < datetime.now(timezone.utc)
        ):
            messages.error(request, "Please make a payment to post a ticket.")
            return redirect("price")
        if request.method == "POST":
            action = request.POST.get("action")
            if action == "upload":
                ticket_ids = int(request.POST["ticket_id"])
                event_name = request.POST["event_name"]
                venue_name = request.POST["venue_name"]
                event_date = request.POST["event_date"]
                event_time = request.POST["event_time"]
                details = request.POST.get("details", "None")
                details = details if details.strip() else "None"
                mobile = request.POST["mobile"]
                info = request.POST["info"]
                section = request.POST["section"]
                row = request.POST["row"]
                first_seat = int(request.POST["first_seat"])
                last_seat = request.POST.get("last_seat", 0)
                print("Last seat from field ", last_seat)
                updated_last_seat = (first_seat + ticket_ids) - 1
                print("After check last seat ", updated_last_seat)
                approve = False
                post_ticket = PostTickets.objects.create(
                    ticket_id=ticket_ids,
                    event_name=event_name,
                    venue_name=venue_name,
                    event_date=event_date,
                    event_time=event_time,
                    details=details,
                    section=section,
                    info=info,
                    row=row,
                    first_seat=first_seat,
                    last_seat=updated_last_seat,
                    mobile=mobile,
                    approve=approve,
                    views=0,
                    user=request.user,
                )
                if (
                    "location" in request.POST
                    and "favorite_team" in request.POST
                    and "sports" in request.POST
                    and "category" in request.POST
                    and "no_of_tickets" in request.POST
                ):
                    location = request.POST["location"]
                    category = request.POST["category"]
                    sports = request.POST["sports"]
                    favorite_team = request.POST["favorite_team"]
                    no_of_tickets = request.POST["no_of_tickets"] or 0
                    TicketPreference.objects.create(
                        favorite_team=favorite_team,
                        category=category,
                        sports=sports,
                        location=location,
                        no_of_tickets=no_of_tickets,
                        ticket=post_ticket,
                    )
                last_ticket = PostTickets.objects.filter(user=request.user).latest("id")
                last_ticket_id = last_ticket.id
                messages.success(request, "Ticket uploaded successfully!")
                return redirect("info_page", id=last_ticket_id)
        else:
            now_utc = datetime.now(timezone.utc)
            today = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            events = Event.objects.filter(dates__start__dateTime__gte=today)
            events = events.values("name").distinct()
            venues = (
                Venue.objects.exclude(name__isnull=True)
                .exclude(name__exact="Null")
                .values("name")
                .distinct()
            )
            classification = Classification.objects.values("genre_name").distinct()
            residences = Venue.objects.values_list("state__name", flat=True).distinct()
            unique_residences = list(residences)
            return render(
                request,
                "post_ticket.html",
                {
                    "events": events,
                    "venues": venues,
                    "classification": classification,
                    "unique_residences": unique_residences,
                },
            )

    except Exception as e:
        log_exception("Post Ticket View", str(e))


@login_required(login_url="login_page")
def available_tickets(request):
    try:
        search_criteria = request.GET.get("search", "")
        current_datetime = timezone.now()
        thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
        swap_tickets = PostTickets.objects.exclude(user_id=request.user.id)
        user_proposed_from_tickets = ExchangeTicket.objects.filter(
            porpose_from=request.user
        ).values_list("ticket_from_exchange_id", flat=True)
        post_tickets = (
            swap_tickets.exclude(id__in=user_proposed_from_tickets)
            .filter(
                Q(event_date__gt=current_datetime.date())
                | Q(
                    event_date=current_datetime.date(),
                    event_time__gt=thirty_minutes_ago.time(),
                )
            )
            .filter(approve=True)
        )
        if search_criteria:
            post_tickets = post_tickets.filter(
                event_name__icontains=search_criteria
            ).filter(approve=True)
        for ticket in post_tickets:
            ticket.increment_views()
        return render(
            request,
            "available_tickets.html",
            {"post_tickets": post_tickets, "search_criteria": search_criteria},
        )
    except Exception as e:
        log_exception("Available Tickets View", str(e))


@login_required(login_url="login_page")
def exchange_tickets_name(request, name):
    try:
        user_profile = Profile.objects.get(user=request.user)
        post_tickets = PostTickets.objects.filter(user_id=request.user.id)
        if not user_profile.is_payment or (
            user_profile.payment_expiration_date
            and user_profile.payment_expiration_date < datetime.now(timezone.utc)
        ):
            messages.error(request, "Please make a payment to post a ticket.")
            return redirect("price")
        if not post_tickets:
            messages.error(request, "Please Post Ticket First")
            return redirect("post_ticket")
        else:
            post_tickets = PostTickets.objects.filter(user_id=request.user.id)
            current_datetime = timezone.now()
            thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
            post_tickets = post_tickets.filter(
                Q(event_date__gt=current_datetime.date())
                | Q(
                    event_date=current_datetime.date(),
                    event_time__gt=thirty_minutes_ago.time(),
                )
            )
            post_ticket = post_tickets.last()
            if post_ticket and not post_ticket.approve:
                approved_tickets = post_tickets.filter(approve=True)
                if approved_tickets.exists():
                    post_ticket = approved_tickets[0]
                else:
                    messages.error(request, "You have not approved tickets!")
                    return redirect("my_tickets")

            if not post_ticket:
                messages.error(request, "You have not posted any tickets!")
                return redirect("my_tickets")
            ticket_preference = post_ticket.ticketpreference
            swap_tickets = PostTickets.objects.exclude(user_id=request.user.id)
            user_proposed_from_tickets = ExchangeTicket.objects.filter(
                porpose_from=request.user
            ).values_list("ticket_from_exchange_id", flat=True)
            swap_tickets = swap_tickets.exclude(id__in=user_proposed_from_tickets)
            swap_tickets = swap_tickets.filter(
                Q(event_date__gt=current_datetime.date())
                | Q(
                    event_date=current_datetime.date(),
                    event_time__gt=thirty_minutes_ago.time(),
                )
            )
            swap_tickets1 = swap_tickets.filter(event_name=name, approve=True)
            for ticket in swap_tickets1:
                ticket.increment_views()
            post_ticket.increment_views()
            return render(
                request,
                "exchange_from_available_tickets.html",
                {"post_ticket": post_ticket, "swap_tickets": swap_tickets1},
            )
    except Exception as e:
        messages.error(request, "Please post ticket first!")
        log_exception("Exchange Ticket Name View", str(e))
        return redirect("post_ticket")


@login_required(login_url="login_page")
def exchange_tickets(request):
    try:
        # user_profile = Profile.objects.get(user=request.user)
        try:
            user_profile = Profile.objects.get(user_id=request.user.id)
        except Profile.DoesNotExist:
            user_profile = Profile.objects.create(user_id=request.user.id)
        if not user_profile.is_payment or (
            user_profile.payment_expiration_date
            and user_profile.payment_expiration_date < datetime.now(timezone.utc)
        ):
            messages.error(request, "Please make a payment to post a ticket.")
            return redirect("price")
        else:
            post_tickets = PostTickets.objects.filter(user_id=request.user.id)
            current_datetime = timezone.now()
            thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
            post_tickets = post_tickets.filter(
                Q(event_date__gt=current_datetime.date())
                | Q(
                    event_date=current_datetime.date(),
                    event_time__gt=thirty_minutes_ago.time(),
                )
            )
            if post_tickets == []:
                messages.error(request, "You have expired tickets! Please post new one")
                return redirect("dashboard")
            post_ticket = post_tickets.last()
            if post_ticket and not post_ticket.approve:
                approved_tickets = post_tickets.filter(approve=True)
                if approved_tickets.exists():
                    post_ticket = approved_tickets[0]
                    post_ticket.increment_views()
                else:
                    messages.error(request, "You have not approved tickets!")
                    return redirect("my_tickets")
            if not post_ticket:
                messages.error(request, "You have not posted any tickets!")
                return redirect("my_tickets")
            ticket_preference = post_ticket.ticketpreference
            swap_tickets = PostTickets.objects.exclude(user_id=request.user.id)
            user_proposed_from_tickets = ExchangeTicket.objects.filter(
                porpose_from=request.user
            ).values_list("ticket_from_exchange_id", flat=True)
            current_datetime = timezone.now()
            thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
            swap_tickets = swap_tickets.exclude(
                id__in=user_proposed_from_tickets
            ).filter(
                Q(event_date__gt=current_datetime.date())
                | Q(
                    event_date=current_datetime.date(),
                    event_time__gt=thirty_minutes_ago.time(),
                )
            )
            swap_tickets1 = swap_tickets.filter(
                event_name=ticket_preference.favorite_team, approve=True
            )
            if not swap_tickets1:
                swap_tickets1 = swap_tickets.exclude(id__in=user_proposed_from_tickets)
                swap_tickets1 = swap_tickets1.filter(approve=True)
            # Increment views for each ticket when the page is loaded
            for ticket in swap_tickets1:
                ticket.increment_views()
            return render(
                request,
                "exchange_tickets.html",
                {
                    "post_ticket": post_ticket,
                    "swap_tickets": swap_tickets1,
                },
            )
    except Exception as e:
        log_exception("Exchange Tickets View", str(e))


@login_required(login_url="login_page")
def request_exchange_tickets(request, id):
    try:
        user_profile = Profile.objects.get(user=request.user)
        if not user_profile.is_payment or (
            user_profile.payment_expiration_date
            and user_profile.payment_expiration_date < datetime.now(timezone.utc)
        ):
            messages.error(request, "Please make a payment to post a ticket.")
            return redirect("price")
        else:
            post_tickets = PostTickets.objects.filter(user_id=request.user.id)
            current_datetime = timezone.now()
            thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
            post_tickets = post_tickets.filter(
                Q(event_date__gt=current_datetime.date())
                | Q(
                    event_date=current_datetime.date(),
                    event_time__gt=thirty_minutes_ago.time(),
                )
            )
            post_ticket = post_tickets.last()
            if post_ticket and not post_ticket.approve:
                approved_tickets = post_tickets.filter(approve=True)
                if approved_tickets.exists():
                    post_ticket = approved_tickets[0]
                else:
                    messages.error(request, "You have not approved tickets!")
                    return redirect("my_tickets")
            if not post_ticket:
                messages.error(request, "You have not posted any tickets!")
                return redirect("my_tickets")
            ticket_preference = post_ticket.ticketpreference
            swap_tickets = PostTickets.objects.exclude(user_id=request.user.id)
            user_proposed_from_tickets = ExchangeTicket.objects.filter(
                porpose_from=request.user
            ).values_list("ticket_from_exchange_id", flat=True)
            swap_tickets = swap_tickets.exclude(id__in=user_proposed_from_tickets)
            swap_tickets1 = swap_tickets.filter(id=id)
            for ticket in swap_tickets1:
                ticket.increment_views()
            post_ticket.increment_views()
            return render(
                request,
                "exchange_from_available_tickets.html",
                {
                    "post_ticket": post_ticket,
                    "swap_tickets": swap_tickets1,
                },
            )
    except Exception as e:
        messages.error(request, "Please post ticket first!")
        log_exception("Request Exchange Ticket View", str(e))
        return redirect("post_ticket")


@login_required(login_url="login_page")
def user_tickets(request, id=None, event_id=None):
    post_tickets = PostTickets.objects.filter(user_id=request.user.id)
    current_datetime = timezone.now()
    thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
    post_tickets = post_tickets.filter(
        Q(event_date__gt=current_datetime.date())
        | Q(
            event_date=current_datetime.date(), event_time__gt=thirty_minutes_ago.time()
        )
    )
    post_tickets = post_tickets.filter(approve=True)
    return render(request, "user_post_tickets.html", {"post_tickets": post_tickets})


@login_required(login_url="login_page")
def user_available_tickets(request, id=None, event_id=None, ticket_id=None):
    post_tickets = PostTickets.objects.filter(user_id=request.user.id)
    current_datetime = timezone.now()
    thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
    post_tickets = post_tickets.filter(
        Q(event_date__gt=current_datetime.date())
        | Q(
            event_date=current_datetime.date(), event_time__gt=thirty_minutes_ago.time()
        )
    )
    post_tickets = post_tickets.filter(approve=True)
    return render(
        request, "user_post_tickets_available.html", {"post_tickets": post_tickets}
    )


@login_required(login_url="login_page")
def specific_user_tickets(request, id, ticket_id):
    post_ticket = PostTickets.objects.get(id=ticket_id)
    if post_ticket.approve:
        post_ticket = PostTickets.objects.get(id=ticket_id)
    else:
        messages.error(request, "This ticket is not approved by admin!")
        return redirect("my_tickets")
    swap_tickets = PostTickets.objects.exclude(user_id=request.user.id)
    user_proposed_from_tickets = ExchangeTicket.objects.filter(
        porpose_from=request.user
    ).values_list("ticket_from_exchange_id", flat=True)
    swap_tickets = swap_tickets.exclude(id__in=user_proposed_from_tickets)
    swap_tickets = swap_tickets.filter(id=id)
    if swap_tickets:
        swap_tickets = swap_tickets.filter(approve=True)
    else:
        swap_tickets = swap_tickets.exclude(id__in=user_proposed_from_tickets)
    for ticket in swap_tickets:
        ticket.increment_views()
    post_ticket.increment_views()
    return render(
        request,
        "exchange_tickets.html",
        {
            "post_ticket": post_ticket,
            "swap_tickets": swap_tickets,
        },
    )


@login_required(login_url="login_page")
def exchange_specific_ticket(request, id):
    try:
        post_ticket = PostTickets.objects.get(id=id)
        if post_ticket.approve:
            post_ticket = PostTickets.objects.get(id=id)
        else:
            messages.error(request, "This ticket is not approved by admin!")
            return redirect("my_tickets")
        current_datetime = timezone.now()
        thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
        swap_tickets = PostTickets.objects.exclude(user_id=request.user.id)
        user_proposed_from_tickets = ExchangeTicket.objects.filter(
            porpose_from=request.user
        ).values_list("ticket_from_exchange_id", flat=True)
        swap_tickets = swap_tickets.exclude(id__in=user_proposed_from_tickets).filter(
            Q(event_date__gt=current_datetime.date())
            | Q(
                event_date=current_datetime.date(),
                event_time__gt=thirty_minutes_ago.time(),
            )
        )
        swap_tickets = swap_tickets.filter(approve=True)
        for ticket in swap_tickets:
            ticket.increment_views()
        post_ticket.increment_views()
        return render(
            request,
            "exchange_tickets.html",
            {
                "post_ticket": post_ticket,
                "swap_tickets": swap_tickets,
            },
        )
    except Exception as e:
        log_exception("Exchange Specific Tickets View", str(e))


@login_required(login_url="login_page")
def swap_ticket(request):
    try:
        if request.method == "POST":
            ticket1_id = request.POST["ticket1"]
            ticket2_id = request.POST.get("ticket2", 0)
            if ticket2_id == 0:
                messages.error(request, "Swap ticket not available!")
                return redirect("exchange_tickets")
            ticket1 = PostTickets.objects.get(id=ticket1_id)
            ticket2 = PostTickets.objects.get(id=ticket2_id)
            user2 = request.user
            user1 = ticket2.user
            profile = Profile.objects.get(user_id=user1.id)
            profile.total_requests += 1
            profile.save()
            exchange = ExchangeTicket(
                porpose_to=user1,
                porpose_from=user2,
                ticket_to_exchange=ticket1,
                ticket_from_exchange=ticket2,
            )
            exchange.save()
            try:
                profile = Profile.objects.get(id=user1.id)
                domain = request.build_absolute_uri("/")
                exchange_request_mail(domain, user1.email, ticket2_id)
            except Exception as e:
                print(e)
            messages.success(request, "Request sent successfully!")
            return redirect("dashboard")
    except Exception as e:
        log_exception("Swap Ticket View", str(e))


@login_required(login_url="login_page")
def mytickets(request):
    try:
        user = request.user
        approved_exchange_tickets = ApprovedExchange.objects.filter(
            Q(transfer_user_1=user) | Q(transfer_user_2=user)
        )
        tickets_from_approved_exchange = []
        admin_approval_tickets = []
        for entry in approved_exchange_tickets:
            if (
                entry.transfer_user_1 == request.user
                and entry.transfer_user_1_ticket not in tickets_from_approved_exchange
            ):
                tickets_from_approved_exchange.append(entry.transfer_user_1_ticket)
                if entry.admin_approval:
                    admin_approval_tickets.append(entry.transfer_user_1_ticket)

            if (
                entry.transfer_user_2 == request.user
                and entry.transfer_user_2_ticket not in tickets_from_approved_exchange
            ):
                tickets_from_approved_exchange.append(entry.transfer_user_2_ticket)
                if entry.admin_approval:
                    admin_approval_tickets.append(entry.transfer_user_2_ticket)
        tickets = PostTickets.objects.filter(user=user.id)
        exchange_tickets1 = ExchangeTicket.objects.filter(porpose_to=user)
        exchange_tickets = []
        for exchange_ticket in exchange_tickets1:
            if (
                exchange_ticket.ticket_to_exchange.event_date == datetime.now().date()
                or exchange_ticket.ticket_from_exchange.event_date
                == datetime.now().date()
            ):
                print(exchange_ticket)
                exchange_ticket.delete()
            else:
                exchange_tickets.append(exchange_ticket)
                print(exchange_tickets)

        sent_exchange_tickets = ExchangeTicket.objects.filter(porpose_from=user)
        if request.method == "POST":
            ticket_id = request.POST["ticketid"]
            ticket = ExchangeTicket.objects.get(id=ticket_id)
            ticket.delete()
        return render(
            request,
            "mytickets.html",
            {
                "tickets": tickets,
                "exchange_tickets": exchange_tickets,
                "approved_exchange_tickets": approved_exchange_tickets,
                "admin_approval_tickets": admin_approval_tickets,
                "sent_exchange_tickets": sent_exchange_tickets,
            },
        )
    except Exception as e:
        log_exception("Myn Tickets View", str(e))


@login_required(login_url="login_page")
def pending_ticket(request):
    try:
        user = request.user
        approved_exchange_tickets = ApprovedExchange.objects.filter(
            Q(transfer_user_1=user) | Q(transfer_user_2=user)
        )
        tickets_from_approved_exchange = []
        admin_approval_tickets = []
        for entry in approved_exchange_tickets:
            if (
                entry.transfer_user_1 == request.user
                and entry.transfer_user_1_ticket not in tickets_from_approved_exchange
            ):
                tickets_from_approved_exchange.append(entry.transfer_user_1_ticket)
                if entry.admin_approval:
                    admin_approval_tickets.append(entry.transfer_user_1_ticket)

            if (
                entry.transfer_user_2 == request.user
                and entry.transfer_user_2_ticket not in tickets_from_approved_exchange
            ):
                tickets_from_approved_exchange.append(entry.transfer_user_2_ticket)
                if entry.admin_approval:
                    admin_approval_tickets.append(entry.transfer_user_2_ticket)
        tickets = PostTickets.objects.filter(user=user.id)
        exchange_tickets1 = ExchangeTicket.objects.filter(porpose_to=user)
        exchange_tickets = []
        for exchange_ticket in exchange_tickets1:
            if (
                exchange_ticket.ticket_to_exchange.event_date == datetime.now().date()
                or exchange_ticket.ticket_from_exchange.event_date
                == datetime.now().date()
            ):
                print(exchange_ticket)
                exchange_ticket.delete()
            else:
                exchange_tickets.append(exchange_ticket)
                print(exchange_tickets)
        sent_exchange_tickets = ExchangeTicket.objects.filter(porpose_from=user)
        if request.method == "POST":
            ticket_id = request.POST["ticketid"]
            ticket = ExchangeTicket.objects.get(id=ticket_id)
            ticket.delete()
        return render(
            request,
            "pending_tickets.html",
            {
                "tickets": tickets,
                "exchange_tickets": exchange_tickets,
                "approved_exchange_tickets": approved_exchange_tickets,
                "admin_approval_tickets": admin_approval_tickets,
                "sent_exchange_tickets": sent_exchange_tickets,
            },
        )
    except Exception as e:
        log_exception("Pending Tickets View", str(e))


def approve_exchange(request, id):
    try:
        user_profile = Profile.objects.get(user=request.user)
        exchange_ticket = get_object_or_404(ExchangeTicket, id=id)
        ticket_to_exchange = PostTickets.objects.get(
            id=exchange_ticket.ticket_to_exchange.id
        )

        ticket_from_exchange = PostTickets.objects.get(
            id=exchange_ticket.ticket_from_exchange.id
        )
        sent_request_remvove = ExchangeTicket.objects.filter(
            ticket_to_exchange=ticket_from_exchange
        ).delete()
        exchange_requests_from_remove = ExchangeTicket.objects.filter(
            ticket_from_exchange=ticket_to_exchange
        ).delete()
        exchange_requests_froms_remove = ExchangeTicket.objects.filter(
            ticket_from_exchange=ticket_from_exchange
        ).delete()
        print(sent_request_remvove)
        ticket_name = ticket_to_exchange.event_name
        PostTickets.objects.filter(id=ticket_to_exchange.id).update(
            user=ticket_from_exchange.user
        )
        PostTickets.objects.filter(id=ticket_from_exchange.id).update(
            user=ticket_to_exchange.user
        )
        ApprovedExchange.objects.create(
            transfer_user_1=request.user,
            transfer_user_2=exchange_ticket.porpose_from,
            transfer_user_1_ticket=ticket_to_exchange,
            transfer_user_2_ticket=ticket_from_exchange,
            admin_approval=False,
        )
        try:
            recipient_email = exchange_ticket.porpose_from.email
            domain = request.build_absolute_uri("/")
            exchange_request_approve_mail(domain, recipient_email, id)
        except Exception as e:
            print(e)
        exchange_ticket.delete()
        user_profile.total_exchanges += 1
        user_profile.save()
        History.objects.create(
            user=request.user,
            action=f"Approved Exchange Ticket# {ticket_to_exchange.id}",
            ticket_name=ticket_name,
        )
        exchange_requests_to_remove = ExchangeTicket.objects.filter(
            ticket_from_exchange=ticket_from_exchange, porpose_to=request.user
        )
        for exchange_request in exchange_requests_to_remove:
            recipient_email = exchange_request.porpose_from.email
            try:
                domain = request.build_absolute_uri("/")
                exchange_request_decline_mail(domain, recipient_email, id)
            except:
                pass
        exchange_requests_to_remove.delete()

        exchange_requests_to_remove = ExchangeTicket.objects.filter(
            ticket_to_exchange=ticket_to_exchange
        )
        for exchange_request in exchange_requests_to_remove:
            recipient_email = exchange_request.porpose_from.email
            try:
                domain = request.build_absolute_uri("/")
                exchange_request_decline_mail(domain, recipient_email, id)
            except:
                pass
        exchange_requests_to_remove.delete()
        return redirect("my_tickets")
    except Exception as e:
        log_exception("Approve Exchange Ticket View", str(e))


def decline_exchange(request, ticket_id):
    try:
        exchange_ticket = ExchangeTicket.objects.get(id=ticket_id)
        ticket_name = exchange_ticket.ticket_to_exchange.event_name
        try:
            recipient_email = exchange_ticket.porpose_from.email
            domain = request.build_absolute_uri("/")
            exchange_request_decline_mail(domain, recipient_email, ticket_id)
        except Exception as e:
            print(e)
        ExchangeTicket.objects.get(id=ticket_id).delete()
        History.objects.create(
            user=request.user,
            action=f"Declined Exchange Ticket# {exchange_ticket.ticket_to_exchange.id}",
            ticket_name=ticket_name,
        )
        return redirect("my_tickets")
    except Exception as e:
        log_exception("Decline Exchnage View", str(e))


@login_required(login_url="login_page")
def discard_exchange(request, ticket_id):
    try:
        exchange_ticket = get_object_or_404(ExchangeTicket, id=ticket_id)
        if exchange_ticket.porpose_from != request.user:
            return redirect("mytickets")
        exchange_ticket.delete()
        messages.error(request, "Request discard sucessfully!")
        return redirect("my_tickets")
    except Exception as e:
        log_exception("Discard Exchange View", str(e))


@login_required(login_url="login_page")
def event_search(request):
    try:
        user = request.user
        exchange_tickets = ExchangeTicket.objects.filter(porpose_to=user).count()
        query = request.GET.get("q")
        now_utc = datetime.now(timezone.utc)
        today = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        venues = Venue.objects.filter(
            event__dates__start__dateTime__gte=today
        ).order_by("event__dates__start__dateTime")
        venues = venues.filter(event__name__icontains=query)
        venues_per_page = 10
        paginator = Paginator(venues, venues_per_page)
        page = request.GET.get("page")
        try:
            venues_page = paginator.page(page)
        except PageNotAnInteger:
            venues_page = paginator.page(1)
        except EmptyPage:
            venues_page = paginator.page(paginator.num_pages)
        return render(
            request,
            "event_search.html",
            {
                "venues": venues_page,
                "query": query,
                "exchange_tickets": exchange_tickets,
                "paginator": paginator,
            },
        )
    except Exception as e:
        log_exception("Event search View", str(e))


class LiveSearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("query", "")
        results = (
            Event.objects.filter(name__icontains=query).values("name").distinct()[:5]
        )
        return JsonResponse(list(results), safe=False)


class EventAutocomplete(View):
    def get(self, request):
        query = request.GET.get("term", "")
        events = Event.objects.filter(name__icontains=query)[:10]
        unique_events = set()
        for event in events:
            unique_events.add(event.name)
        results = [
            {"label": event_name, "value": event_name} for event_name in unique_events
        ]
        return JsonResponse(results, safe=False)


def swap_tickets_by_day(request):
    selected_day = request.GET.get("selected_day", None)
    selected_event_type = request.GET.get("selected_event_type", None)
    if not selected_day or selected_day not in [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]:
        return JsonResponse({"error": "Invalid day selected"}, status=400)
    current_datetime = timezone.now()
    thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
    swap_tickets = PostTickets.objects.exclude(user_id=request.user.id)
    user_proposed_from_tickets = ExchangeTicket.objects.filter(
        porpose_from=request.user
    ).values_list("ticket_from_exchange_id", flat=True)
    swap_tickets = swap_tickets.exclude(id__in=user_proposed_from_tickets).filter(
        Q(event_date__gt=current_datetime.date())
        | Q(
            event_date=current_datetime.date(), event_time__gt=thirty_minutes_ago.time()
        )
    )
    swap_tickets = swap_tickets.filter(approve=True)
    if selected_day and not selected_event_type:
        swap_tickets = swap_tickets.annotate(
            selected_day=F("event_date__week_day") - 1
        ).filter(selected_day=day_of_week(selected_day))
        swap_tickets = swap_tickets.filter(approve=True)
    if selected_day and selected_event_type:
        swap_tickets = swap_tickets.annotate(
            selected_day=F("event_date__week_day") - 1
        ).filter(
            selected_day=day_of_week(selected_day),
            ticketpreference__sports=selected_event_type,
        )
        swap_tickets = swap_tickets.filter(approve=True)
    return render(request, "search_tickets.html", {"swap_tickets": swap_tickets})


def day_of_week(day_name):
    days = {
        "Monday": 1,
        "Tuesday": 2,
        "Wednesday": 3,
        "Thursday": 4,
        "Friday": 5,
        "Saturday": 6,
        "Sunday": 7,
    }
    return days.get(day_name, 0)


@require_GET
def load_all_swap_tickets(request):
    try:
        current_datetime = timezone.now()
        thirty_minutes_ago = current_datetime - timezone.timedelta(minutes=30)
        swap_tickets = PostTickets.objects.exclude(user_id=request.user.id)
        user_proposed_from_tickets = ExchangeTicket.objects.filter(
            porpose_from=request.user
        ).values_list("ticket_from_exchange_id", flat=True)
        swap_tickets = swap_tickets.exclude(id__in=user_proposed_from_tickets).filter(
            Q(event_date__gt=current_datetime.date())
            | Q(
                event_date=current_datetime.date(),
                event_time__gt=thirty_minutes_ago.time(),
            )
        )
        swap_tickets = swap_tickets.filter(approve=True)
        return render(request, "search_tickets.html", {"swap_tickets": swap_tickets})
    except Exception as e:
        log_exception("Load all Tickets View", str(e))


def get_dates_and_times_for_event_and_venue(request, event_name, venue_name):
    try:
        event_name = event_name.replace("<", "/")
        now_utc = datetime.now(timezone.utc)
        today = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        events = Event.objects.filter(
            name=event_name, dates__start__localDate__gte=today
        )
        venues = Venue.objects.filter(name=venue_name)

        if events.exists() and venues.exists():
            all_dates_times = []
            for event in events:
                for venue in venues:
                    if venue.event == event:
                        dates = event.dates
                        if dates:
                            if isinstance(dates, dict):
                                start_info = dates.get("start", {})
                                local_date = start_info.get("localDate", "")
                                local_time = start_info.get("localTime", "")
                                if local_date and local_time:
                                    all_dates_times.append(
                                        {"date": local_date, "time": local_time}
                                    )
                            elif isinstance(dates, str):
                                date_info = json.loads(dates)
                                start_info = date_info.get("start", {})
                                local_date = start_info.get("localDate", "")
                                local_time = start_info.get("localTime", "")
                                if local_date and local_time:
                                    all_dates_times.append(
                                        {"date": local_date, "time": local_time}
                                    )

            sorted_dates_times = sorted(all_dates_times, key=itemgetter("date"))

            return JsonResponse({"all_dates_times": sorted_dates_times})
        else:
            return JsonResponse({"error": "Event or Venue not found"}, status=404)
    except Exception as e:
        log_exception("Get Dates and Times for Events View", str(e))
        return JsonResponse({"error": "An error occurred"}, status=500)


@login_required(login_url="login_page")
def history(request):
    # print(save_states_and_cities())
    # import_cities_data()
    return render(request, "history.html", {"history": History.objects.filter(user=request.user)})


# Payment Views
@login_required(login_url="login_page")
def price(request):
    try:
        try:
            profile = Profile.objects.get(user_id=request.user.id)

        except Profile.DoesNotExist:
            profile = Profile.objects.create(user_id=request.user.id)
        return render(request, "price.html", {"profile": profile})
    except Exception as e:
        log_exception("Price View", str(e))


@csrf_exempt
def stripe_config(request):
    try:
        if request.method == "GET":
            stripe_config = {"publicKey": settings.STRIPE_PUBLISHABLE_KEY}
            return JsonResponse(stripe_config, safe=False)
    except Exception as e:
        log_exception("Stripe Config View", str(e))


@login_required(login_url="login_page")
@csrf_exempt
def create_checkout_session(request):
    try:
        if request.method == "GET":
            domain_url = request.build_absolute_uri("/")
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                user_profile = Profile.objects.get(user=request.user)
                if not user_profile.stripe_customer_id:
                    customer = stripe.Customer.create(
                        email=request.user.email,
                    )
                    Profile.objects.filter(id=user_profile.id).update(
                        stripe_customer_id=customer.id
                    )
                    print(f"new saved id {user_profile.stripe_customer_id}")
                if user_profile.stripe_customer_id:
                    user_profile.stripe_customer_id = user_profile.stripe_customer_id
                    print(f"old saved id {user_profile.stripe_customer_id}")
                if user_profile.free_trail:
                    price_id = os.environ.get("PRICE_KEY")
                    trial_days = None
                else:
                    price_id = os.environ.get("PRICE_KEY")
                    trial_days = 7
                user_profile = Profile.objects.get(user=request.user)
                print(user_profile.stripe_customer_id)
                checkout_session = stripe.checkout.Session.create(
                    success_url=domain_url + "success",
                    cancel_url=domain_url + "cancelled/",
                    payment_method_types=["card"],
                    mode="subscription",
                    customer=user_profile.stripe_customer_id,
                    line_items=[
                        {
                            "price": os.environ.get("PRICE_KEY"),
                            "quantity": 1,
                        }
                    ],
                    # discounts=[{"coupon": "kh6lUvWs"}],
                    subscription_data={
                        "trial_period_days": trial_days,
                    },
                    allow_promotion_codes=True,
                )
                return JsonResponse({"sessionId": checkout_session["id"]})
            except Exception as e:
                return JsonResponse({"error": str(e)})
    except Exception as e:
        log_exception("Create Checkout session View", str(e))


@login_required(login_url="login_page")
def success_payment(request):
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        user_profile = Profile.objects.get(user=request.user)
        print(user_profile.stripe_customer_id)
        upcoming_invoices = stripe.Invoice.list(
            customer=str(user_profile.stripe_customer_id)
        )
        print("Coming Invoice ", upcoming_invoices)
        for invoice in upcoming_invoices["data"]:
            period_end = invoice["lines"]["data"][0]["period"]["end"]
            print("End of subscription period:", period_end)
            break
        datetime_obj = datetime.utcfromtimestamp(period_end)
        expiration_date = make_aware(datetime_obj)
        print("Convert date and Time ", expiration_date)
        user_profile.is_payment = True
        user_profile.payment_expiration_date = expiration_date
        user_profile.free_trail = True
        user_profile.cancel_subscription = False
        user_profile.save()
        recipient_email = request.user.email
        try:
            domain = request.build_absolute_uri("/")
            payment_reciept_mail(domain, recipient_email)
        except:
            pass
        messages.success(request, "Congrats! You can now upload and exchange tickets.")
        return redirect("dashboard")
    except Exception as e:
        print("Sucess Payment View", str(e))


def cancel_payment(request):
    try:
        messages.error(request, "Operation was not successful")
        return render(request, "dashboard.html")
    except Exception as e:
        log_exception("Cancel Payment View", str(e))


def cancel_subscription(request):
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        user_profile = Profile.objects.get(user=request.user)
        subscriptions = stripe.Subscription.list(
            customer=user_profile.stripe_customer_id
        )
        print(subscriptions.data[0].id)
        stripe.Subscription.delete(subscriptions.data[0].id)
        # stripe.Customer.delete(user_profile.stripe_customer_id)
        # user_profile.stripe_customer_id=None
        user_profile.cancel_subscription = True
        # user_profile.payment_expiration_date=None
        user_profile.save()
        messages.error(request, "Subscription cancelled successfully!")
        return redirect("dashboard")
    except Exception as e:
        log_exception("Subscription cancelled View", str(e))


def discard_exchange(request, ticket_id):
    try:
        exchange_ticket = get_object_or_404(ExchangeTicket, id=ticket_id)
        if exchange_ticket.porpose_from != request.user:
            return redirect("mytickets")
        exchange_ticket.delete()
        messages.error(request, "Request discard sucessfully!")
        return redirect("my_tickets")
    except Exception as e:
        log_exception("Discard Exchange View", str(e))


def delete_ticket(request, id):
    try:
        post_ticket = PostTickets.objects.get(id=id).delete()
        messages.success(request, "Your's ticket deleted successfully!")
        return redirect("my_tickets")
    except Exception as e:
        log_exception("Delete Ticket View", str(e))


def check_subscription(user):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    user_profile = Profile.objects.get(user=user)
    if not user_profile.stripe_customer_id and user_profile.is_payment:
        return True
    if user_profile.stripe_customer_id:
        try:
            upcoming_invoices = stripe.Invoice.list(
                customer=str(user_profile.stripe_customer_id)
            )
            for invoice in upcoming_invoices["data"]:
                period_end = invoice["lines"]["data"][0]["period"]["end"]
                print("End of subscription period:", period_end)
                datetime_obj = datetime.utcfromtimestamp(period_end)
                expiration_date = make_aware(datetime_obj)
                print("Convert date and Time ", expiration_date)  # get from the stripe.
                current_date_time = datetime.now(UTC)
                print("Today Date is ", current_date_time)
                if expiration_date < current_date_time:
                    print("Subscription has expired.")
                    user_profile.is_payment = False
                    user_profile.payment_expiration_date = expiration_date
                    user_profile.free_trail = False
                    user_profile.save()
                    return False
                elif expiration_date > current_date_time:
                    print("I have subscription now")
                    user_profile.is_payment = True
                    user_profile.payment_expiration_date = expiration_date
                    user_profile.free_trail = True
                    user_profile.save()
                    return True
            # If no upcoming invoices found
            print("No upcoming invoices found.")
            return True
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            print("Stripe API error:", str(e))
            return True
    else:
        print("Stripe customer ID not available.")
        return False
