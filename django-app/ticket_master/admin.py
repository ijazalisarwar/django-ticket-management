from django.contrib import admin

from .models import Classification, Event, Venue

# Register your models here.

admin.site.register(Event)
admin.site.register(Classification)
admin.site.register(Venue)
