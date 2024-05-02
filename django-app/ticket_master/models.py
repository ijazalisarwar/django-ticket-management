from django.contrib.auth.models import User
from django.db import models


class Event(models.Model):
    event_id = models.CharField(max_length=80, null=True, unique=True)
    name = models.CharField(max_length=180, null=True)
    type = models.CharField(max_length=150, null=True)
    locale = models.CharField(max_length=110, null=True)
    url = models.URLField(max_length=200, null=True)
    sales = models.JSONField(null=True)
    dates = models.JSONField(null=True)
    please_note = models.TextField(null=True)
    price_range = models.JSONField(null=True)
    promoter = models.JSONField(null=True)
    images = models.JSONField(null=True)
    info = models.TextField(null=True)
    description = models.TextField(null=True)
    promoters = models.JSONField(null=True)
    outlets = models.JSONField(null=True)
    products = models.JSONField(null=True)
    seatmap = models.JSONField(null=True)
    accessibility = models.JSONField(null=True)
    ticket_limit = models.JSONField(null=True)
    external_links = models.JSONField(null=True)
    aliases = models.JSONField(null=True)
    localized_aliases = models.JSONField(null=True)
    venue_id = models.CharField(max_length=140, null=True)
    venue_name = models.CharField(max_length=280, null=True)
    venue_type = models.CharField(max_length=150, null=True)
    venue_locale = models.CharField(max_length=50, null=True)
    venue_url = models.URLField(max_length=200, null=True)
    venue_location = models.JSONField(null=True)
    venue_markets = models.JSONField(null=True)
    venue_timezone = models.CharField(max_length=200, null=True)
    venue_address = models.JSONField(null=True)
    venue_city = models.JSONField(null=True)
    venue_state = models.JSONField(null=True)
    venue_country = models.JSONField(null=True)
    venue_postal_code = models.CharField(max_length=50, null=True)
    venue_dmas = models.JSONField(null=True)
    genre_name = models.CharField(max_length=100, default="")
    segment_name = models.CharField(max_length=100, default="")
    views = models.IntegerField(default=0)

    def increment_views(self):
        self.views += 1
        self.save()


class Venue(models.Model):
    venue_id = models.CharField(max_length=100)
    name = models.CharField(max_length=180, null=True)
    type = models.CharField(max_length=150, null=True)
    locale = models.CharField(max_length=50, null=True)
    location = models.JSONField()
    timezone = models.CharField(max_length=200, null=True)
    address = models.JSONField()
    city = models.JSONField()
    state = models.JSONField()
    country = models.JSONField()
    postal_code = models.CharField(max_length=100, null=True)
    dmas = models.JSONField()
    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name="venues",
        to_field="event_id",
        unique=True,
    )


class Classification(models.Model):
    genre_name = models.CharField(max_length=100, default="")
    segment_name = models.CharField(max_length=100, default="")
    family = models.BooleanField(null=True)


class Ticket(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
