from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    middle_name = models.CharField(max_length=30)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    street_address = models.CharField(max_length=150)
    apartment_number = models.CharField(max_length=50)
    city = models.CharField(max_length=20)
    dob = models.DateField(null=True)
    state = models.CharField(max_length=30)
    mobile = models.CharField(max_length=18)
    is_payment = models.BooleanField(default=False)
    complete_profile = models.BooleanField(default=False)
    forget_password_tocken = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    tm_email = models.EmailField(null=True)
    payment_expiration_date = models.DateTimeField(null=True)
    total_requests = models.IntegerField(default=0, null=True)
    total_exchanges = models.IntegerField(default=0, null=True)
    zip_code = models.CharField(max_length=10, null=True)
    promo_code = models.CharField(max_length=50, null=True)
    free_trail = models.BooleanField(default=False)
    cancel_subscription = models.BooleanField(default=False)


class LogEntry(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    view_name = models.CharField(max_length=255)
    error_message = models.TextField()

    def __str__(self):
        return self.view_name


class UserPreferences(models.Model):
    sports = models.CharField(max_length=3000, default="")
    music = models.CharField(max_length=3000, default="")
    art = models.CharField(max_length=3000, default="")
    family = models.CharField(max_length=3000, default="")
    no_of_tickets = models.BooleanField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class DeletedTickets(models.Model):
    ticket_id = models.CharField(max_length=100)
    event_name = models.CharField(max_length=300)
    venue_name = models.CharField(max_length=300)
    event_date = models.DateField(blank=True, null=True)
    event_time = models.TimeField(default="")
    details = models.TextField(blank=True, null=True)
    mobile = models.CharField(max_length=300, null=True)
    info = models.CharField(max_length=300, null=True)
    section = models.CharField(max_length=300, null=True)
    row = models.CharField(max_length=300, null=True)
    first_seat = models.IntegerField(null=True)
    last_seat = models.IntegerField(null=True)
    approve = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.event_name} - Deleted"


class PostTickets(models.Model):
    ticket_id = models.CharField(max_length=100)
    event_name = models.CharField(max_length=300)
    venue_name = models.CharField(max_length=300)
    event_date = models.DateField(blank=True, null=True)
    event_time = models.TimeField(default="")
    details = models.TextField(blank=True, null=True)
    mobile = models.CharField(max_length=300, null=True)
    info = models.CharField(max_length=300, null=True)
    section = models.CharField(max_length=300, null=True)
    row = models.CharField(max_length=300, null=True)
    first_seat = models.IntegerField(null=True)
    last_seat = models.IntegerField(null=True)
    approve = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    is_update = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def increment_views(self):
        self.views += 1
        self.save()

    def __str__(self):
        review_status = "Approved!" if self.approve else "In Review"
        return f"{self.event_name} - {review_status}"

    def delete(self, *args, **kwargs):
        # Save a copy of the ticket to the DeletedTickets table
        DeletedTickets.objects.create(
            ticket_id=self.ticket_id,
            event_name=self.event_name,
            venue_name=self.venue_name,
            event_date=self.event_date,
            event_time=self.event_time,
            details=self.details,
            mobile=self.mobile,
            info=self.info,
            section=self.section,
            row=self.row,
            first_seat=self.first_seat,
            last_seat=self.last_seat,
            approve=self.approve,
            views=self.views,
            user=self.user,
        )
        super(PostTickets, self).delete(*args, **kwargs)


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    ticket_name = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"


class TicketPreference(models.Model):
    favorite_team = models.CharField(max_length=100, null=True)
    category = models.CharField(max_length=100, null=True)
    sports = models.CharField(max_length=100, null=True)
    location = models.CharField(max_length=100, null=True)
    no_of_tickets = models.IntegerField(null=True)
    ticket = models.OneToOneField(PostTickets, on_delete=models.CASCADE)


class ExchangeTicket(models.Model):
    porpose_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="proposed_to_tickets"
    )
    porpose_from = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="proposed_from_tickets"
    )
    ticket_to_exchange = models.ForeignKey(
        PostTickets, on_delete=models.CASCADE, related_name="exchange_ticket_to"
    )
    ticket_from_exchange = models.ForeignKey(
        PostTickets, on_delete=models.CASCADE, related_name="exchange_ticket_from"
    )


class ApprovedExchange(models.Model):
    transfer_user_1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transfer_user_1", null=True
    )
    transfer_user_2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transfer_user_2", null=True
    )
    transfer_user_1_ticket = models.ForeignKey(
        PostTickets,
        on_delete=models.CASCADE,
        related_name="transfer_user_1_ticket",
        null=True,
    )
    transfer_user_2_ticket = models.ForeignKey(
        PostTickets,
        on_delete=models.CASCADE,
        related_name="transfer_user_2_ticket",
        null=True,
    )
    admin_approval = models.BooleanField(default=False)


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField()
    created_time = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    image = models.ImageField(upload_to="blog_images/")

    def __str__(self):
        return self.title


class State(models.Model):
    name = models.CharField(max_length=255)
    geoname_id = models.IntegerField(null=True)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=255)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}, {self.state.name}"


class ContactUs(models.Model):
    name = models.CharField(max_length=300)
    email = models.EmailField()
    description = models.TextField()

    def __str__(self):
        return f"{self.name}, {self.email}"


class NewsLetter(models.Model):
    name = models.CharField(max_length=300)
    email = models.EmailField()

    def __str__(self):
        return f"{self.name}, {self.email}"


class PromoCode(models.Model):
    promo_code = models.CharField(max_length=50)

    def __str__(self):
        return self.promo_code


class StaffActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(
        max_length=10,
        choices=(
            ("CREATE", "Create"),
            ("READ", "Read"),
            ("UPDATE", "Update"),
            ("DELETE", "Delete"),
        ),
    )
    model_name = models.CharField(max_length=100)
    ticket_name = models.CharField(max_length=400, blank=True)
    read = models.BooleanField(default=False)
    object_id = models.PositiveIntegerField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.model_name} - {self.object_id}"
